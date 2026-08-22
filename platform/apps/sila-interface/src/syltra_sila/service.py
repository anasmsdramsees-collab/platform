"""SILA interface (spec §14.10).

SILA explains, asks, and collects answers. It does not decide and it does not
act. Every mutating intent is routed through the Policy and Safety Service, and
`SilaService` holds no device gateway — so "SILA cannot bypass policy" is a
property of its dependencies, not a rule someone has to remember.

The one intent that could change a device, `REQUEST_CAPABILITY_CHANGE`, is
deliberately the longest path in this file: it builds a `Recommendation`,
submits it to policy, and reports whatever policy said. If policy asks for
approval, SILA says so; it does not approve on the user's behalf.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from syltra_api_gateway.platform import Platform
from syltra_api_gateway.translations import is_rtl, translate_reason, translate_reasons
from syltra_contracts import (
    FeedbackKind,
    FeedbackSource,
    ModelReference,
    PolicyOutcome,
    Recommendation,
    RecommendationTarget,
)
from syltra_security import (
    AuthorizationError,
    Permission,
    Principal,
    authorize,
    authorize_capability,
)
from syltra_sila.intents import SILA_VERSION, IntentType, SilaIntent, SilaResponse
from syltra_sila.phrases import phrase

logger = logging.getLogger(__name__)

MANUAL_REQUEST_TTL = timedelta(minutes=5)


class SilaRefused(PermissionError):
    """SILA declined an intent — with a reason the user can be told."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code


@dataclass
class SilaService:
    """Turns structured intents into answers and policy submissions."""

    platform: Platform

    def __post_init__(self) -> None:
        # Asserted, not merely intended: SILA holds no path to a device.
        for forbidden in ("gateway", "orchestrator_gateway", "device_client"):
            if hasattr(self, forbidden):
                msg = f"SILA must not hold {forbidden}"
                raise RuntimeError(msg)

    @property
    def version(self) -> str:
        return SILA_VERSION

    def handle(
        self, intent: SilaIntent, principal: Principal, now: datetime | None = None
    ) -> SilaResponse:
        """Handle one intent. Authorization first, always."""
        moment = now or datetime.now(tz=UTC)
        try:
            authorize(principal, intent.home_id, Permission.READ_HOME)
        except AuthorizationError as exc:
            raise SilaRefused(exc.code, str(exc)) from exc

        handlers = {
            IntentType.REPORT_HOME_STATUS: self._report_home_status,
            IntentType.REPORT_RISK_STATUS: self._report_risk_status,
            IntentType.LIST_RECOMMENDATIONS: self._list_recommendations,
            IntentType.EXPLAIN_RECOMMENDATION: self._explain_recommendation,
            IntentType.EXPLAIN_DECISION: self._explain_decision,
            IntentType.APPROVE_RECOMMENDATION: self._approve,
            IntentType.REJECT_RECOMMENDATION: self._reject,
            IntentType.SUBMIT_FEEDBACK: self._submit_feedback,
            IntentType.REQUEST_CAPABILITY_CHANGE: self._request_change,
        }
        return handlers[intent.intent](intent, principal, moment)

    # ── read-only intents ──

    def _report_home_status(
        self, intent: SilaIntent, principal: Principal, now: datetime
    ) -> SilaResponse:
        snapshot = self.platform.twin.snapshot(intent.home_id, now)
        contexts = self.platform.context.active(intent.home_id, now)
        online = sum(1 for d in snapshot.devices.values() if d["available"] is not False)
        return self._respond(
            intent,
            speech=phrase(
                "home_status",
                intent.locale,
                devices=len(snapshot.devices),
                online=online,
                contexts=len(contexts),
            ),
            data={
                "devices": len(snapshot.devices),
                "devices_online": online,
                "rooms": len(snapshot.rooms),
                "contexts": [
                    {
                        "type": c.context_type.value,
                        "scope": c.scope,
                        "confidence": c.confidence,
                        "reasons": translate_reasons(c.reason_codes, intent.locale),
                    }
                    for c in contexts
                ],
            },
        )

    def _report_risk_status(
        self, intent: SilaIntent, principal: Principal, now: datetime
    ) -> SilaResponse:
        cases = self.platform.risk.open_cases(intent.home_id, now)
        confirmed = [c for c in cases if c.permits_emergency_response]
        watching = [c for c in cases if c.is_advisory]
        if confirmed:
            speech = phrase(
                "risk_confirmed", intent.locale, category=confirmed[0].category.value
            )
        elif watching:
            speech = phrase("risk_watching", intent.locale, count=len(watching))
        else:
            speech = phrase("risk_clear", intent.locale)
        return self._respond(
            intent,
            speech=speech,
            data={
                "confirmed": [
                    {
                        "category": c.category.value,
                        "severity": c.severity.value,
                        "confirmed_by": c.confirmed_by,
                        "reasons": translate_reasons(c.reason_codes, intent.locale),
                    }
                    for c in confirmed
                ],
                # Advisory cases are labelled as such wherever they surface, so
                # a household is never told a watch is a confirmed emergency.
                "watching": [
                    {
                        "category": c.category.value,
                        "advisory": True,
                        "reasons": translate_reasons(c.reason_codes, intent.locale),
                    }
                    for c in watching
                ],
            },
        )

    def _list_recommendations(
        self, intent: SilaIntent, principal: Principal, now: datetime
    ) -> SilaResponse:
        live = [
            r
            for r in self.platform.adaptive.build_recommendations(intent.home_id, now)
            if not r.shadow and not r.is_expired_at(now)
        ]
        return self._respond(
            intent,
            speech=phrase("recommendation_count", intent.locale, count=len(live)),
            data={
                "recommendations": [
                    {
                        "recommendation_id": str(r.recommendation_id),
                        "type": r.recommendation_type,
                        "device_id": r.target.device_id,
                        "capability": r.target.capability,
                        "proposed_value": r.proposed_value,
                        "confidence": r.confidence,
                        "reasons": translate_reasons(r.reason_codes, intent.locale),
                    }
                    for r in live
                ]
            },
        )

    def _explain_recommendation(
        self, intent: SilaIntent, principal: Principal, now: datetime
    ) -> SilaResponse:
        if intent.recommendation_id is None:
            raise SilaRefused("MISSING_RECOMMENDATION_ID", "no recommendation identified")
        for record in self.platform.adaptive.build_recommendations(intent.home_id, now):
            if record.recommendation_id == intent.recommendation_id:
                reasons = translate_reasons(record.reason_codes, intent.locale)
                return self._respond(
                    intent,
                    speech=phrase(
                        "explain_recommendation",
                        intent.locale,
                        value=record.proposed_value,
                        reason=reasons[0] if reasons else "",
                    ),
                    reason_codes=record.reason_codes,
                    reasons=reasons,
                    requires_approval=record.requires_user_approval,
                    data={
                        "proposed_value": record.proposed_value,
                        "confidence": record.confidence,
                        "model": {
                            "name": record.model.name,
                            "version": record.model.version,
                        },
                        "expires_at": record.expires_at.isoformat(),
                    },
                )
        raise SilaRefused("RECOMMENDATION_NOT_FOUND", "no such recommendation")

    def _explain_decision(
        self, intent: SilaIntent, principal: Principal, now: datetime
    ) -> SilaResponse:
        if intent.decision_id is None:
            raise SilaRefused("MISSING_DECISION_ID", "no decision identified")
        decision = self.platform.policy.get(intent.decision_id)
        if decision is None or decision.home_id != intent.home_id:
            raise SilaRefused("DECISION_NOT_FOUND", "no such decision")
        reasons = translate_reasons(decision.reason_codes, intent.locale)
        return self._respond(
            intent,
            speech=phrase(
                "explain_decision",
                intent.locale,
                outcome=translate_reason(decision.decision.value, intent.locale),
                reason=reasons[0] if reasons else "",
            ),
            reason_codes=decision.reason_codes,
            reasons=reasons,
            policy_decision=decision.decision.value,
            data={
                "safety_class": decision.safety_class.value,
                "evaluated_at": decision.evaluated_at.isoformat(),
                "expires_at": decision.expires_at.isoformat(),
            },
        )

    # ── responses to proposals ──

    def _approve(
        self, intent: SilaIntent, principal: Principal, now: datetime
    ) -> SilaResponse:
        self._require(principal, intent.home_id, Permission.APPROVE_RECOMMENDATION)
        decision = self._pending_decision(intent)
        try:
            approved = self.platform.policy.approve(
                decision.decision_id, actor=principal.subject, now=now
            )
        except ValueError as exc:
            raise SilaRefused("APPROVAL_NOT_POSSIBLE", str(exc)) from exc
        return self._respond(
            intent,
            speech=phrase("approved", intent.locale),
            reason_codes=approved.reason_codes,
            reasons=translate_reasons(approved.reason_codes, intent.locale),
            policy_decision=approved.decision.value,
            data={"decision_id": str(approved.decision_id)},
        )

    def _reject(
        self, intent: SilaIntent, principal: Principal, now: datetime
    ) -> SilaResponse:
        self._require(principal, intent.home_id, Permission.APPROVE_RECOMMENDATION)
        decision = self._pending_decision(intent)
        denied = self.platform.policy.reject(
            decision.decision_id, actor=principal.subject, now=now
        )
        return self._respond(
            intent,
            speech=phrase("rejected", intent.locale),
            reason_codes=denied.reason_codes,
            reasons=translate_reasons(denied.reason_codes, intent.locale),
            policy_decision=denied.decision.value,
        )

    def _submit_feedback(
        self, intent: SilaIntent, principal: Principal, now: datetime
    ) -> SilaResponse:
        if intent.recommendation_id is None:
            raise SilaRefused("MISSING_RECOMMENDATION_ID", "no recommendation identified")
        try:
            kind = FeedbackKind(str(intent.feedback_kind or "").upper())
        except ValueError as exc:
            raise SilaRefused(
                "UNKNOWN_FEEDBACK_KIND", f"{intent.feedback_kind!r} is not a feedback kind"
            ) from exc
        record = self.platform.feedback.record(
            home_id=intent.home_id,
            recommendation_id=intent.recommendation_id,
            kind=kind,
            # Feedback through SILA is a person speaking, never an echo.
            source=FeedbackSource.USER,
            actor=principal.subject,
            modified_value=intent.value,
            now=now,
        )
        if kind is FeedbackKind.NEVER_REPEAT:
            for suppressed in self.platform.feedback.suppressed_types(intent.home_id):
                self.platform.policy.suppress(intent.home_id, suppressed)
        return self._respond(
            intent,
            speech=phrase("feedback_recorded", intent.locale, kind=kind.value),
            data={"feedback_id": str(record.feedback_id), "kind": kind.value},
        )

    # ── the one intent that could change something ──

    def _request_change(
        self, intent: SilaIntent, principal: Principal, now: datetime
    ) -> SilaResponse:
        """A deliberate manual request — still routed through policy.

        Spec §0 rule 16 gives manual control precedence, but precedence is not
        the same as bypass: the request becomes a recommendation, policy decides,
        and SILA reports the decision. Nothing here reaches a device.
        """
        if not intent.device_id or not intent.capability:
            raise SilaRefused("INCOMPLETE_REQUEST", "a device and capability are required")
        try:
            authorize_capability(principal, intent.home_id, intent.capability)
        except AuthorizationError as exc:
            raise SilaRefused(exc.code, str(exc)) from exc

        proposal = Recommendation(
            recommendation_id=uuid4(),
            home_id=intent.home_id,
            recommendation_type=f"manual.{intent.capability}",
            created_at=now,
            expires_at=now + MANUAL_REQUEST_TTL,
            target=RecommendationTarget(
                device_id=intent.device_id, capability=intent.capability
            ),
            proposed_value=intent.value,
            confidence=1.0,  # the user is certain; policy still decides
            reason_codes=["USER_REQUESTED"],
            model=ModelReference(name="sila.manual", version=SILA_VERSION),
            required_policy="COMFORT_AUTOMATION",
            requires_user_approval=False,
        )
        twin_device = self.platform.twin.device(intent.home_id, intent.device_id)
        current = (
            twin_device.capability(intent.capability) if twin_device is not None else None
        )
        decision = self.platform.policy.evaluate(
            proposal,
            now=now,
            twin_value=current.value if current else None,
            twin_status=current.status_at(now).value if current else "UNKNOWN",
        )
        reasons = translate_reasons(decision.reason_codes, intent.locale)
        speech_key = {
            PolicyOutcome.ALLOW: "request_allowed",
            PolicyOutcome.DENY: "request_denied",
            PolicyOutcome.REQUIRE_USER_APPROVAL: "request_needs_approval",
            PolicyOutcome.PREPARE_ONLY: "request_deferred",
            PolicyOutcome.ESCALATE_TO_FIXED_SAFETY_RULE: "request_escalated",
        }[decision.decision]
        return self._respond(
            intent,
            speech=phrase(
                speech_key, intent.locale, reason=reasons[0] if reasons else ""
            ),
            reason_codes=decision.reason_codes,
            reasons=reasons,
            requires_approval=decision.decision is PolicyOutcome.REQUIRE_USER_APPROVAL,
            # Never True here: SILA submits to policy; the Action Orchestrator
            # executes, and only from an approved decision.
            executed=False,
            policy_decision=decision.decision.value,
            data={
                "decision_id": str(decision.decision_id),
                "recommendation_id": str(proposal.recommendation_id),
            },
        )

    # ── helpers ──

    def _require(self, principal: Principal, home_id: str, permission: Permission) -> None:
        try:
            authorize(principal, home_id, permission)
        except AuthorizationError as exc:
            raise SilaRefused(exc.code, str(exc)) from exc

    def _pending_decision(self, intent: SilaIntent) -> Any:
        if intent.recommendation_id is None:
            raise SilaRefused("MISSING_RECOMMENDATION_ID", "no recommendation identified")
        for decision in reversed(list(self.platform.policy.decisions.values())):
            if (
                decision.home_id == intent.home_id
                and decision.recommendation_id == intent.recommendation_id
                and decision.decision is PolicyOutcome.REQUIRE_USER_APPROVAL
            ):
                return decision
        raise SilaRefused("NO_PENDING_APPROVAL", "nothing is waiting for your answer")

    def _respond(
        self,
        intent: SilaIntent,
        speech: str,
        data: dict[str, Any] | None = None,
        reason_codes: list[str] | None = None,
        reasons: list[str] | None = None,
        requires_approval: bool = False,
        executed: bool = False,
        policy_decision: str | None = None,
    ) -> SilaResponse:
        return SilaResponse(
            intent=intent.intent,
            home_id=intent.home_id,
            locale=intent.locale,
            direction="rtl" if is_rtl(intent.locale) else "ltr",
            speech=speech,
            data=data or {},
            reason_codes=reason_codes or [],
            reasons=reasons or [],
            requires_approval=requires_approval,
            executed=executed,
            policy_decision=policy_decision,
        )
