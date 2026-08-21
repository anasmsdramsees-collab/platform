"""Local API Gateway (spec §14.9, §21).

The only publicly exposed SYLTRA service. Every endpoint is authenticated,
home-scoped, and returns view models composed from the in-process services —
never raw internal state.

Reason codes are translated here and nowhere else (spec §21), so the machine
identifiers stay stable for audit while the wording is free to change. Every
response that carries reason codes carries both: `reason_codes` for machines and
`reasons` for people.
"""

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated, Any
from uuid import UUID

from fastapi import Body, FastAPI, Query, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from syltra_api_gateway import metrics
from syltra_api_gateway.dependencies import (
    CorrelationDep,
    LocaleDep,
    PrincipalDep,
    RateLimiter,
    check_approve,
    check_audit,
    check_automations,
    check_users,
    check_models,
    check_read,
    get_rate_limiter,
)
from syltra_api_gateway.energy import Resolution
from syltra_api_gateway.errors import bad_request, conflict, forbidden, not_found
from syltra_api_gateway.platform import Platform
from syltra_api_gateway.stream import HEARTBEAT_SECONDS
from syltra_api_gateway.translations import is_rtl, translate_reasons
from pydantic import ValidationError
from syltra_action_orchestrator import ActionRefused, build_manual_action
from syltra_contracts import (
    Automation,
    ConditionKind,
    ContextType,
    FeedbackKind,
    FeedbackSource,
    PolicyOutcome,
    TriggerKind,
)
from syltra_contracts.automations import AUTOMATABLE_SAFETY_CLASSES, MINIMUM_REARM
from syltra_contracts.capability_definitions import Access, get_definition
from syltra_digital_twin.core import StateStatus
from syltra_policy_safety.service import PolicyService
from syltra_security import (
    ROLE_PERMISSIONS,
    permission_for_capability,
    MembershipRefused,
    Permission,
    Role,
    TokenStore,
    may_see_capability,
)

API_VERSION = "1.0"


def _console_directory() -> Path | None:
    """Locate the console's static files, if they are present.

    Returns None rather than raising when they are absent, so the API is
    usable in a headless deployment or a test that only exercises endpoints.
    """
    candidate = Path(__file__).resolve().parents[4] / "apps" / "local-console" / "static"
    return candidate if candidate.is_dir() else None


def _panel_directory() -> Path | None:
    """The wall panel's static files.

    A separate app rather than a mode of the console, because it is a separate
    product: the console is somebody at a laptop deciding, and the panel is
    anybody walking past. Sharing a codebase would make every console change a
    change to a screen in somebody's hallway.
    """
    candidate = Path(__file__).resolve().parents[4] / "apps" / "wall-panel" / "static"
    return candidate if candidate.is_dir() else None


def _design_system_directory() -> Path | None:
    """Locate the generated design-system CSS, if it is present.

    Mounted separately from the console because the console mount claims
    `/console/*` wholesale; a nested mount there would never be reached.
    """
    candidate = (
        Path(__file__).resolve().parents[4]
        / "apps"
        / "local-console"
        / "src"
        / "design-system"
    )
    return candidate if candidate.is_dir() else None


def _paginate(items: list[Any], limit: int, offset: int) -> dict[str, Any]:
    """Uniform pagination envelope (spec §21)."""
    window = items[offset : offset + limit]
    return {
        "items": window,
        "total": len(items),
        "limit": limit,
        "offset": offset,
        "has_more": offset + len(window) < len(items),
    }


def create_app(
    platform: Platform,
    tokens: TokenStore | None = None,
    rate_limiter: RateLimiter | None = None,
) -> FastAPI:
    app = FastAPI(
        title="SYLTRA Local API",
        version=API_VERSION,
        description=(
            "Local, authenticated API for the SYLTRA Adaptive Edge Platform. "
            "All endpoints are home-scoped; no internal transport or storage "
            "details are exposed."
        ),
        docs_url="/v1/docs",
        openapi_url="/v1/openapi.json",
    )
    app.state.platform = platform

    @app.middleware("http")
    async def _publish_changes(request: Request, call_next: Any) -> Response:
        """Wake the stream after any request that changed something.

        Middleware rather than a line in each handler, because a line in each
        handler is a line the next handler forgets. Every successful mutating
        request against a home publishes, whatever route added it.

        A dry run is excluded by name: it is a POST that changes nothing, and a
        notification for it would make the console re-read for no reason.
        """
        response: Response = await call_next(request)
        if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
            return response
        if response.status_code >= 400 or request.url.path.endswith("/dry-run"):
            return response
        home_id = request.path_params.get("home_id") or request.query_params.get("home_id")
        if not home_id:
            return response
        # The path is the reason, uppercased: APPROVE, REJECT, ENABLED. It is
        # what changed, in the vocabulary the caller already used.
        tail = [part for part in request.url.path.rsplit("/", 2)[-2:] if part]
        reason = (tail[-1] if tail else "UPDATED").upper()
        request.app.state.platform.stream.publish(str(home_id), reason)
        return response
    # `is None`, not `or`: TokenStore defines __len__, so an empty store is
    # falsy and `tokens or TokenStore()` would silently discard the caller's
    # store — every token it later issued would then be unknown to this app.
    app.state.tokens = TokenStore() if tokens is None else tokens
    app.state.rate_limiter = RateLimiter() if rate_limiter is None else rate_limiter

    # The console is static files served by the gateway (ADR-007): no Node
    # runtime on the hub, and no second origin to authorize.
    design_system_root = _design_system_directory()
    if design_system_root is not None:
        app.mount(
            "/design-system",
            StaticFiles(directory=design_system_root),
            name="design-system",
        )

    panel_root = _panel_directory()
    if panel_root is not None:
        app.mount("/panel", StaticFiles(directory=panel_root, html=True), name="panel")

    console_root = _console_directory()
    if console_root is not None:
        app.mount(
            "/console", StaticFiles(directory=console_root, html=True), name="console"
        )

    @app.middleware("http")
    async def attach_correlation_id(request: Request, call_next: Any) -> Response:
        response: Response = await call_next(request)
        incoming = request.headers.get("X-Correlation-ID")
        if incoming:
            response.headers["X-Correlation-ID"] = incoming
        return response

    # ── health and system ──

    @app.get("/health/live", tags=["system"])
    async def live() -> dict[str, str]:
        return {"status": "alive"}

    @app.get("/health/ready", tags=["system"])
    async def ready() -> dict[str, str]:
        return {"status": "ready"}

    @app.get("/v1/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "api_version": API_VERSION}

    @app.get("/metrics", tags=["system"])
    async def prometheus_metrics() -> Response:
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.get("/v1/me", tags=["system"])
    async def whoami(principal: PrincipalDep) -> dict[str, Any]:
        """Who the caller is, and the scope their token carries.

        The console needs this to filter navigation and to populate the
        property selector. It reports nothing the caller could not already
        determine by trying every endpoint — and guidelines §3 is explicit
        that hiding a control is not authorization: every endpoint still
        checks scope and permission on each request.

        `homes` is the token's own scope, not a directory: it cannot be used
        to discover a household the caller is not a member of.
        """
        return {
            "subject": principal.subject,
            "display_name": principal.display_name,
            "role": principal.role.value,
            "permissions": sorted(p.value for p in principal.permissions),
            "homes": sorted(principal.home_ids),
        }

    @app.get("/v1/system/status", tags=["system"])
    async def system_status(principal: PrincipalDep) -> dict[str, Any]:
        return platform.system_status()

    # ── twin, rooms, devices ──

    @app.get("/v1/homes/{home_id}/twin", tags=["home"])
    async def get_twin(home_id: str, principal: PrincipalDep) -> dict[str, Any]:
        check_read(home_id, principal)
        now = datetime.now(tz=UTC)
        snapshot = platform.twin.snapshot(home_id, now)
        return {
            "home_id": home_id,
            "taken_at": snapshot.taken_at.isoformat(),
            "devices": snapshot.devices,
            "rooms": snapshot.rooms,
            "events_applied": snapshot.events_applied,
        }

    @app.get("/v1/homes/{home_id}/rooms", tags=["home"])
    async def get_rooms(home_id: str, principal: PrincipalDep) -> dict[str, Any]:
        check_read(home_id, principal)
        snapshot = platform.twin.snapshot(home_id, datetime.now(tz=UTC))
        return {
            "home_id": home_id,
            "rooms": [
                {"room_id": room, "device_ids": devices, "device_count": len(devices)}
                for room, devices in sorted(snapshot.rooms.items())
            ],
        }

    def _without_unseeable(device: dict[str, Any], principal: Any) -> dict[str, Any]:
        """Strip capabilities this caller may not be shown.

        Filtered out of the payload rather than blanked, because a key present
        with a null value still tells the reader the camera exists and that
        somebody decided they may not see it. Whether a room has a camera is
        itself the kind of thing a property company should not learn from a
        device list.

        A device left with no visible capabilities is still listed: hiding the
        device would make a hub look like it has fewer devices than it does.
        """
        capabilities = device.get("capabilities")
        if not isinstance(capabilities, dict):
            return device
        visible: dict[str, Any] = {}
        for name, reading in capabilities.items():
            if not may_see_capability(principal, name):
                continue
            visible[name] = {**reading, "operable": _operable_by(principal, name)}
        return {**device, "capabilities": visible}

    def _operable_by(principal: Any, capability: str) -> bool:
        """Whether *this caller* may switch this, answered by the server.

        A client cannot work this out without a copy of the capability
        registry, and a second copy is one that drifts — so a wall panel asking
        "what can I press" gets the answer rather than deriving it. The field
        answers "can you", not "is it writable", because that is the question a
        screen is actually asking: a motion sensor and a lock are both
        unpressable from a hallway panel, for entirely different reasons, and
        the panel does not need to know which.
        """
        definition = get_definition(capability)
        if definition.access is Access.READ:
            return False
        allowed: bool = principal.may(permission_for_capability(capability))
        return allowed

    @app.get("/v1/homes/{home_id}/devices", tags=["home"])
    async def get_devices(
        home_id: str,
        principal: PrincipalDep,
        limit: Annotated[int, Query(ge=1, le=200)] = 50,
        offset: Annotated[int, Query(ge=0)] = 0,
        room_id: str | None = None,
    ) -> dict[str, Any]:
        check_read(home_id, principal)
        snapshot = platform.twin.snapshot(home_id, datetime.now(tz=UTC))
        devices = [
            _without_unseeable(device, principal)
            for device in snapshot.devices.values()
            if room_id is None or device["room_id"] == room_id
        ]
        return {"home_id": home_id, **_paginate(devices, limit, offset)}

    # ── contexts ──

    @app.get("/v1/homes/{home_id}/contexts/current", tags=["context"])
    async def current_contexts(
        home_id: str, principal: PrincipalDep, locale: LocaleDep
    ) -> dict[str, Any]:
        check_read(home_id, principal)
        now = datetime.now(tz=UTC)
        records = platform.context.active(home_id, now)
        return {
            "home_id": home_id,
            "locale": locale,
            "direction": "rtl" if is_rtl(locale) else "ltr",
            "evaluated_at": now.isoformat(),
            "contexts": [
                {
                    "context_id": str(record.context_id),
                    "context_type": record.context_type.value,
                    "scope": record.scope,
                    "confidence": record.confidence,
                    "started_at": record.started_at.isoformat(),
                    "expires_at": record.expires_at.isoformat(),
                    "seconds_until_expiry": round(
                        (record.expires_at - now).total_seconds(), 1
                    ),
                    "advisory_only": record.is_advisory_only(),
                    "reason_codes": record.reason_codes,
                    "reasons": translate_reasons(record.reason_codes, locale),
                    "evidence": [
                        {
                            "device_id": item.device_id,
                            "room_id": item.room_id,
                            "capability": item.capability,
                            "value": item.value,
                            "status": item.status,
                            "observed_at": (
                                item.observed_at.isoformat() if item.observed_at else None
                            ),
                        }
                        for item in record.evidence
                    ],
                }
                for record in records
            ],
        }

    # ── recommendations ──

    def _live_decision(home_id: str, recommendation_id: UUID, now: datetime) -> Any:
        """The most recent unexpired decision for this recommendation, if any."""
        for decision in reversed(list(platform.policy.decisions.values())):
            if (
                decision.home_id == home_id
                and decision.recommendation_id == recommendation_id
                and decision.expires_at > now
            ):
                return decision
        return None

    def _policy_decision_for(record: Any, now: datetime) -> Any:
        """Get, or make, the policy decision that governs this recommendation.

        A recommendation the console can see but not act on is worse than no
        recommendation: the approve endpoint looks up a *pending decision*, and
        without this nothing ever creates one, so every approval returned 404.

        Evaluating here rather than at approval time is deliberate. Policy must
        decide before a person is offered the choice — otherwise the console
        would present an approve button for an action policy will refuse, and
        the refusal would arrive as an error after the click. It also means the
        console can show what policy decided and why, which is what makes the
        decision reviewable rather than implicit.

        Shadow recommendations are never evaluated. A shadow prediction is not
        a proposal, and creating an approvable decision for one would be
        exactly the bypass §19.2 forbids.
        """
        if record.shadow:
            return None
        existing = _live_decision(record.home_id, record.recommendation_id, now)
        if existing is not None:
            return existing
        # The twin's own snapshot, not a value carried along from wherever the
        # recommendation was built: policy must judge against what is true now.
        snapshot = platform.twin.snapshot(record.home_id, now)
        device = snapshot.devices.get(record.target.device_id, {})
        reading = device.get("capabilities", {}).get(record.target.capability)
        return platform.policy.evaluate(
            record,
            now=now,
            twin_value=reading["value"] if reading else None,
            twin_status=reading["status"] if reading else "UNKNOWN",
            twin_age_seconds=reading["age_seconds"] if reading else None,
        )

    def _decision_summary(decision: Any, locale: str) -> dict[str, Any] | None:
        if decision is None:
            return None
        return {
            "decision_id": str(decision.decision_id),
            "decision": decision.decision.value,
            "safety_class": decision.safety_class.value,
            "evaluated_at": decision.evaluated_at.isoformat(),
            "expires_at": decision.expires_at.isoformat(),
            "required_approval_from": decision.required_approval_from,
            "reason_codes": decision.reason_codes,
            "reasons": translate_reasons(decision.reason_codes, locale),
        }

    def _recommendation_view(record: Any, locale: str, decision: Any = None) -> dict[str, Any]:
        return {
            "policy": _decision_summary(decision, locale),
            "recommendation_id": str(record.recommendation_id),
            "recommendation_type": record.recommendation_type,
            "target": {
                "device_id": record.target.device_id,
                "capability": record.target.capability,
                "room_id": record.target.room_id,
            },
            "proposed_value": record.proposed_value,
            "confidence": record.confidence,
            "created_at": record.created_at.isoformat(),
            "expires_at": record.expires_at.isoformat(),
            "requires_user_approval": record.requires_user_approval,
            "shadow": record.shadow,
            "model": {"name": record.model.name, "version": record.model.version},
            "reason_codes": record.reason_codes,
            "reasons": translate_reasons(record.reason_codes, locale),
        }

    @app.get("/v1/homes/{home_id}/recommendations", tags=["recommendations"])
    async def list_recommendations(
        home_id: str,
        principal: PrincipalDep,
        locale: LocaleDep,
        limit: Annotated[int, Query(ge=1, le=100)] = 25,
        offset: Annotated[int, Query(ge=0)] = 0,
    ) -> dict[str, Any]:
        check_read(home_id, principal)
        now = datetime.now(tz=UTC)
        live = [
            record
            for record in platform.adaptive.build_recommendations(home_id, now)
            if not record.is_expired_at(now)
        ]
        views = [
            _recommendation_view(record, locale, _policy_decision_for(record, now))
            for record in live
        ]
        return {"home_id": home_id, "locale": locale, **_paginate(views, limit, offset)}

    @app.get(
        "/v1/homes/{home_id}/recommendations/{recommendation_id}", tags=["recommendations"]
    )
    async def get_recommendation(
        home_id: str, recommendation_id: UUID, principal: PrincipalDep, locale: LocaleDep
    ) -> dict[str, Any]:
        check_read(home_id, principal)
        now = datetime.now(tz=UTC)
        for record in platform.adaptive.build_recommendations(home_id, now):
            if record.recommendation_id == recommendation_id:
                return _recommendation_view(record, locale, _policy_decision_for(record, now))
        raise not_found("RECOMMENDATION_NOT_FOUND", "no such recommendation")

    @app.post(
        "/v1/homes/{home_id}/recommendations/{recommendation_id}/approve",
        tags=["recommendations"],
    )
    async def approve_recommendation(
        home_id: str,
        recommendation_id: UUID,
        principal: PrincipalDep,
        locale: LocaleDep,
        correlation: CorrelationDep,
        request: Request,
    ) -> dict[str, Any]:
        check_approve(home_id, principal)
        get_rate_limiter(request).check(principal.subject, "approve")
        decision = _pending_decision(platform.policy, home_id, recommendation_id)
        try:
            approved = platform.policy.approve(decision.decision_id, actor=principal.subject)
        except ValueError as exc:
            raise conflict("APPROVAL_NOT_POSSIBLE", str(exc)) from exc
        metrics.APPROVALS.labels(outcome="approved").inc()
        return _decision_view(approved, locale, correlation)

    @app.post(
        "/v1/homes/{home_id}/recommendations/{recommendation_id}/reject",
        tags=["recommendations"],
    )
    async def reject_recommendation(
        home_id: str,
        recommendation_id: UUID,
        principal: PrincipalDep,
        locale: LocaleDep,
        correlation: CorrelationDep,
        request: Request,
    ) -> dict[str, Any]:
        check_approve(home_id, principal)
        get_rate_limiter(request).check(principal.subject, "reject")
        decision = _pending_decision(platform.policy, home_id, recommendation_id)
        denied = platform.policy.reject(decision.decision_id, actor=principal.subject)
        metrics.APPROVALS.labels(outcome="rejected").inc()
        return _decision_view(denied, locale, correlation)

    @app.post(
        "/v1/homes/{home_id}/recommendations/{recommendation_id}/feedback",
        tags=["recommendations"],
    )
    async def submit_feedback(
        home_id: str,
        recommendation_id: UUID,
        principal: PrincipalDep,
        request: Request,
        payload: Annotated[dict[str, Any], Body()],
    ) -> dict[str, Any]:
        check_read(home_id, principal)
        get_rate_limiter(request).check(principal.subject, "feedback")
        raw = str(payload.get("kind", "")).upper()
        try:
            kind = FeedbackKind(raw)
        except ValueError:
            raise bad_request(
                "UNKNOWN_FEEDBACK_KIND",
                f"{raw!r} is not a feedback kind",
                allowed=[k.value for k in FeedbackKind],
            ) from None
        record = platform.feedback.record(
            home_id=home_id,
            recommendation_id=recommendation_id,
            kind=kind,
            # Feedback arriving through the API is always a person acting
            # deliberately; automation echoes never reach this path.
            source=FeedbackSource.USER,
            actor=principal.subject,
            modified_value=payload.get("modified_value"),
        )
        metrics.FEEDBACK.labels(kind=kind.value).inc()
        return {
            "feedback_id": str(record.feedback_id),
            "kind": record.kind.value,
            "recorded_at": record.recorded_at.isoformat(),
        }

    # ── risks ──

    @app.get("/v1/homes/{home_id}/risks", tags=["risk"])
    async def list_risks(
        home_id: str, principal: PrincipalDep, locale: LocaleDep
    ) -> dict[str, Any]:
        check_read(home_id, principal)
        now = datetime.now(tz=UTC)
        return {
            "home_id": home_id,
            "locale": locale,
            "direction": "rtl" if is_rtl(locale) else "ltr",
            "cases": [_risk_view(case, locale) for case in platform.risk.open_cases(home_id, now)],
        }

    @app.get("/v1/homes/{home_id}/risks/{case_id}", tags=["risk"])
    async def get_risk(
        home_id: str, case_id: UUID, principal: PrincipalDep, locale: LocaleDep
    ) -> dict[str, Any]:
        check_read(home_id, principal)
        for case in platform.risk.open_cases(home_id, datetime.now(tz=UTC)):
            if case.case_id == case_id:
                return _risk_view(case, locale)
        raise not_found("RISK_CASE_NOT_FOUND", "no such risk case")

    # ── actions ──

    @app.get("/v1/homes/{home_id}/actions/{action_id}", tags=["actions"])
    async def get_action(
        home_id: str, action_id: UUID, principal: PrincipalDep, locale: LocaleDep
    ) -> dict[str, Any]:
        check_read(home_id, principal)
        for result in platform.orchestrator.results(home_id):
            if result.action_id == action_id:
                return {
                    "action_id": str(result.action_id),
                    "status": result.status.value,
                    "attempts": result.attempt_count,
                    "observed_value": result.observed_value,
                    "compensated": result.compensated,
                    "completed_at": result.completed_at.isoformat(),
                    "reason_codes": result.reason_codes,
                    "reasons": translate_reasons(result.reason_codes, locale),
                }
        raise not_found("ACTION_NOT_FOUND", "no such action")

    @app.get("/v1/homes/{home_id}/actions", tags=["actions"])
    async def list_actions(
        home_id: str,
        principal: PrincipalDep,
        locale: LocaleDep,
        limit: Annotated[int, Query(ge=1, le=100)] = 25,
        offset: Annotated[int, Query(ge=0)] = 0,
    ) -> dict[str, Any]:
        check_read(home_id, principal)
        views = [
            {
                "action_id": str(result.action_id),
                "status": result.status.value,
                "completed_at": result.completed_at.isoformat(),
                "reason_codes": result.reason_codes,
                "reasons": translate_reasons(result.reason_codes, locale),
            }
            for result in reversed(platform.orchestrator.results(home_id))
        ]
        return {"home_id": home_id, **_paginate(views, limit, offset)}

    # ── models ──

    @app.get("/v1/homes/{home_id}/models", tags=["models"])
    async def list_models(home_id: str, principal: PrincipalDep) -> dict[str, Any]:
        check_read(home_id, principal)
        return {
            "home_id": home_id,
            "learning_mode": platform.adaptive.mode(home_id).value,
            "models": [
                {
                    "name": version.name,
                    "version": version.version,
                    "status": version.status.value,
                    "model_type": version.model_type.value,
                    "evaluation_metrics": version.evaluation_metrics,
                    "promoted_at": (
                        version.promoted_at.isoformat() if version.promoted_at else None
                    ),
                }
                for version in platform.adaptive.registry.versions(home_id)
            ],
        }

    @app.post("/v1/homes/{home_id}/models/{name}/suspend", tags=["models"])
    async def suspend_model(
        home_id: str,
        name: str,
        principal: PrincipalDep,
        request: Request,
        payload: Annotated[dict[str, str] | None, Body()] = None,
    ) -> dict[str, Any]:
        options = payload or {}
        check_models(home_id, principal)
        get_rate_limiter(request).check(principal.subject, "suspend_model")
        try:
            version = platform.adaptive.registry.suspend(
                home_id, name,
                reason=options.get("reason", "suspended by operator"),
                actor=principal.subject,
            )
        except RuntimeError as exc:
            raise conflict("NO_ACTIVE_VERSION", str(exc)) from exc
        return {"name": version.name, "version": version.version, "status": version.status.value}

    # ── automations (spec §2.3, ADR-009) ──

    def _automation_view(automation: Any, locale: str) -> dict[str, Any]:
        """The §17.8 list fields, plus why it last did nothing.

        `safety_class` is derived from the actions rather than stored, so it
        cannot drift from what the automation would actually touch.
        """
        last = platform.automations.last_fired(automation.home_id, automation.automation_id)
        return {
            "automation_id": str(automation.automation_id),
            "home_id": automation.home_id,
            "name": automation.name,
            "enabled": automation.enabled,
            "source": automation.source.value,
            "safety_class": automation.safety_class.value,
            "summary": automation.summary(),
            "trigger": automation.trigger.model_dump(mode="json", exclude_none=True),
            "conditions": [
                condition.model_dump(mode="json", exclude_none=True)
                for condition in automation.conditions
            ],
            "actions": [
                action.model_dump(mode="json", exclude_none=True)
                for action in automation.actions
            ],
            "rearm_seconds": automation.rearm_seconds,
            "owner": automation.owner,
            "version": automation.version,
            "last_run": last.isoformat() if last else None,
        }

    @app.get("/v1/homes/{home_id}/automations", tags=["automations"])
    async def list_automations(
        home_id: str, principal: PrincipalDep, locale: LocaleDep
    ) -> dict[str, Any]:
        # Reading is part of seeing the home; writing is not.
        check_read(home_id, principal)
        return {
            "home_id": home_id,
            "items": [
                _automation_view(automation, locale)
                for automation in platform.automations.list_for(home_id)
            ],
        }

    # Registered before `/{automation_id}`: FastAPI matches routes in the order
    # they are added, so a literal segment declared after a path parameter is
    # never reached. "options" was being parsed as a UUID and answering 422.
    @app.get("/v1/homes/{home_id}/automations/proposals", tags=["automations"])
    async def automation_proposals(
        home_id: str, principal: PrincipalDep, locale: LocaleDep
    ) -> dict[str, Any]:
        """Standing rules the platform would write, if the household agreed.

        Read-only, and it stays read-only: accepting one means POSTing the
        automation through the ordinary endpoint, so a proposal cannot become a
        rule without passing every check a hand-written automation passes.
        """
        check_read(home_id, principal)
        home = platform.twin.home(home_id)
        devices = list(home.devices.values()) if home is not None else []

        # A rule the household already has must not be offered again. Compared
        # on what the automation *does* rather than on its name or id, because
        # accepting a proposal produces a new automation with neither.
        existing = {
            (
                action.device_id,
                action.capability,
                automation.trigger.at_hour,
                automation.trigger.at_minute,
            )
            for automation in platform.automations.list_for(home_id)
            if automation.trigger.kind is TriggerKind.AT_TIME
            for action in automation.actions
        }

        proposals: list[dict[str, Any]] = []
        for device in devices:
            for proposal in platform.adaptive.propose_automations(home_id, device.device_id):
                if proposal.capability not in device.capabilities:
                    # The routine model tracks one capability across the home;
                    # only offer it against a device that actually has it.
                    continue
                if (
                    proposal.device_id,
                    proposal.capability,
                    proposal.at_hour,
                    proposal.at_minute,
                ) in existing:
                    continue
                view = proposal.as_view()
                view["reason"] = translate_reasons([view["reason_code"]], locale)[0]
                proposals.append(view)
        return {
            "home_id": home_id,
            "proposals": proposals,
            # Said plainly: the platform is offering, not deciding.
            "creates_nothing": True,
        }

    @app.get("/v1/homes/{home_id}/automations/options", tags=["automations"])
    async def automation_options(
        home_id: str, principal: PrincipalDep, locale: LocaleDep
    ) -> dict[str, Any]:
        """Everything a household may build an automation out of.

        Served rather than hard-coded in the console, because the console would
        otherwise carry a second copy of the capability vocabulary and the two
        would drift. This one is derived from the registry and from what the
        home actually has, so a device that is not there cannot be chosen and a
        capability the platform forbids cannot be offered.

        Critical capabilities are absent by construction: `AutomationAction`
        refuses to be built with anything outside NON_CRITICAL and COMFORT, so
        offering a valve here would produce a form whose submission always
        fails. The console says why they are missing rather than hiding the
        fact (§20).
        """
        check_read(home_id, principal)
        home = platform.twin.home(home_id)
        devices = list(home.devices.values()) if home is not None else []

        def describe(device: Any, capability: str) -> dict[str, Any]:
            definition = get_definition(capability)
            return {
                "device_id": device.device_id,
                "room_id": device.room_id,
                "capability": capability,
                "data_type": definition.data_type.value,
                "unit": definition.unit,
                "minimum": definition.minimum,
                "maximum": definition.maximum,
                "allowed_values": list(definition.allowed_values),
            }

        actionable: list[dict[str, Any]] = []
        observable: list[dict[str, Any]] = []
        excluded: list[dict[str, Any]] = []
        for device in devices:
            for capability in sorted(device.capabilities):
                definition = get_definition(capability)
                writable = definition.access in (Access.WRITE, Access.READ_WRITE)
                if writable and definition.safety_class in AUTOMATABLE_SAFETY_CLASSES:
                    actionable.append(describe(device, capability))
                elif writable:
                    # Named, not hidden: a household that cannot automate its
                    # gas valve should be told that is deliberate.
                    excluded.append(
                        {
                            "device_id": device.device_id,
                            "capability": capability,
                            "safety_class": definition.safety_class.value,
                            "reason_code": "CAPABILITY_NOT_AUTOMATABLE",
                            "reason": translate_reasons(["CAPABILITY_NOT_AUTOMATABLE"], locale)[0],
                        }
                    )
                if definition.access in (Access.READ, Access.READ_WRITE):
                    observable.append(describe(device, capability))

        return {
            "home_id": home_id,
            "watch": observable,
            "act_on": actionable,
            "not_automatable": excluded,
            "trigger_kinds": [kind.value for kind in TriggerKind],
            "condition_kinds": [kind.value for kind in ConditionKind],
            "context_types": [context.value for context in ContextType],
            # The engine's own guard rails, so the form can explain a refusal
            # before it happens rather than after.
            "minimum_rearm_seconds": int(MINIMUM_REARM.total_seconds()),
        }

    @app.get("/v1/homes/{home_id}/automations/{automation_id}", tags=["automations"])
    async def get_automation(
        home_id: str, automation_id: UUID, principal: PrincipalDep, locale: LocaleDep
    ) -> dict[str, Any]:
        check_read(home_id, principal)
        automation = platform.automations.get(home_id, automation_id)
        if automation is None:
            raise not_found("AUTOMATION_NOT_FOUND", "no such automation")
        return _automation_view(automation, locale)

    @app.post("/v1/homes/{home_id}/automations", tags=["automations"])
    async def create_automation(
        home_id: str,
        principal: PrincipalDep,
        locale: LocaleDep,
        payload: Annotated[dict[str, Any], Body()],
    ) -> dict[str, Any]:
        check_automations(home_id, principal)
        try:
            automation = Automation(
                **{**payload, "home_id": home_id, "owner": principal.subject}
            )
        except ValidationError as exc:
            # A rejected automation is usually a household trying to do
            # something §2.3 forbids, so the message matters more than usual.
            raise bad_request("INVALID_AUTOMATION", str(exc)) from exc
        stored = platform.automations.upsert(automation)
        return _automation_view(stored, locale)

    @app.post("/v1/homes/{home_id}/automations/{automation_id}/enabled", tags=["automations"])
    async def set_automation_enabled(
        home_id: str,
        automation_id: UUID,
        principal: PrincipalDep,
        locale: LocaleDep,
        payload: Annotated[dict[str, Any], Body()],
    ) -> dict[str, Any]:
        check_automations(home_id, principal)
        enabled = bool(payload.get("enabled", True))
        updated = platform.automations.set_enabled(home_id, automation_id, enabled)
        if updated is None:
            raise not_found("AUTOMATION_NOT_FOUND", "no such automation")
        return _automation_view(updated, locale)

    @app.post("/v1/homes/{home_id}/automations/dry-run", tags=["automations"])
    async def dry_run_automations(
        home_id: str, principal: PrincipalDep, locale: LocaleDep
    ) -> dict[str, Any]:
        """Evaluate every automation against the home as it is, and change nothing.

        §17.8 asks for a test mode. This is it, and it is safe to offer because
        `dry_run` means the engine does not record that anything fired — so a
        test run cannot put a real automation into its re-arm interval.
        """
        check_read(home_id, principal)
        now = datetime.now(tz=UTC)
        snapshot = platform.twin.home(home_id)
        if snapshot is None:
            raise not_found("HOME_NOT_FOUND", "no such home")
        active = [record.context_type.value for record in platform.context.active(home_id, now)]
        result = platform.automations.evaluate(
            home_id, snapshot, now, active_contexts=active, dry_run=True
        )
        return {
            "home_id": home_id,
            "evaluated_at": now.isoformat(),
            "would_run": [
                {
                    "automation_id": str(proposal.automation_id),
                    "name": proposal.name,
                    "capability": proposal.action.capability,
                    "value": proposal.action.value,
                    "device_id": proposal.action.device_id,
                    "expires_at": proposal.expires_at.isoformat(),
                    "reasons": translate_reasons(list(proposal.reason_codes), locale),
                }
                for proposal in result.proposals
            ],
            "would_not_run": [
                {
                    "automation_id": str(automation_id),
                    "reason_code": reason,
                    "reasons": translate_reasons([reason], locale),
                }
                for automation_id, reason in result.skipped
            ],
            "dispatched": False,
        }

    # ── energy over time (spec §17.11, §27 criterion 9) ──

    @app.get("/v1/homes/{home_id}/energy/history", tags=["energy"])
    async def energy_history(
        home_id: str,
        principal: PrincipalDep,
        locale: LocaleDep,
        resolution: Annotated[str, Query(description="minute, hour or day")] = "hour",
        hours: Annotated[int, Query(ge=1, le=24 * 90)] = 24,
        device_id: Annotated[str | None, Query()] = None,
    ) -> dict[str, Any]:
        """Measured power over time, with its gaps named rather than filled.

        Spec §17.11 forbids estimating a measurement, so an interval nothing
        reported in is listed under `missing` instead of appearing as a zero.
        A chart drawn from this has holes, and the holes are the honest part.
        """
        check_read(home_id, principal)
        try:
            bucket_size = Resolution(resolution)
        except ValueError as exc:
            known = ", ".join(r.value for r in Resolution)
            raise bad_request(
                "UNKNOWN_RESOLUTION", f"{resolution!r} is not a resolution. Known: {known}"
            ) from exc

        end = datetime.now(tz=UTC)
        series = platform.energy.series(
            home_id, bucket_size, end - timedelta(hours=hours), end, device_id=device_id
        )
        view = series.as_view()
        earliest = platform.energy.earliest(home_id)
        # A household that has just installed the hub has no history, and that
        # is a different thing from a household whose meter stopped reporting.
        view["recording_since"] = earliest.isoformat() if earliest else None
        return view

    # ── users and roles (spec §21, UI-5) ──

    def _membership_or_404(home_id: str, membership_id: UUID) -> Any:
        for membership in platform.users.members(home_id):
            if membership.membership_id == membership_id:
                return membership
        raise not_found("NO_SUCH_MEMBERSHIP", f"no membership {membership_id}")

    def _required_reason(payload: dict[str, Any]) -> str:
        """UI-5: a permission change carries a reason, or it does not happen.

        Refused here as well as in the directory, so the caller gets a 400 that
        names the field rather than a 500 from a constructor.
        """
        reason = str(payload.get("reason", "")).strip()
        if not reason:
            raise bad_request(
                "REASON_REQUIRED",
                "a change to who may do what has to say why",
            )
        return reason

    def _role_or_400(value: Any) -> Role:
        try:
            return Role(str(value))
        except ValueError as exc:
            known = ", ".join(sorted(r.value for r in Role))
            raise bad_request("UNKNOWN_ROLE", f"{value!r} is not a role. Known: {known}") from exc

    @app.get("/v1/homes/{home_id}/users", tags=["users"])
    async def list_users(
        home_id: str, principal: PrincipalDep, locale: LocaleDep
    ) -> dict[str, Any]:
        # Readable by anyone who may see the home: knowing who else holds a key
        # to the house you live in is not a privileged question.
        check_read(home_id, principal)
        now = datetime.now(tz=UTC)
        # Who manages the property, said on the screen where somebody asks who
        # can see it. A company that can see the devices in the flat you live
        # in is a condition of the tenancy, not something to discover.
        management = (
            platform.organisations.as_view(home_id)
            if platform.organisations is not None
            else {"managed_by": None}
        )
        return {
            "home_id": home_id,
            "management": management,
            "members": [m.as_view(now) for m in platform.users.members(home_id, now)],
            # The console hides controls it cannot use rather than showing
            # buttons that will be refused.
            "may_manage": principal.may(Permission.MANAGE_USERS),
            "assignable_roles": sorted(
                role.value
                for role in Role
                if role is not Role.SERVICE
                and not (ROLE_PERMISSIONS[role] - principal.permissions)
            ),
        }

    @app.post("/v1/homes/{home_id}/users", tags=["users"])
    async def grant_membership(
        home_id: str,
        principal: PrincipalDep,
        locale: LocaleDep,
        payload: Annotated[dict[str, Any], Body()],
    ) -> dict[str, Any]:
        check_users(home_id, principal)
        reason = _required_reason(payload)
        subject = str(payload.get("subject", "")).strip()
        if not subject:
            raise bad_request("SUBJECT_REQUIRED", "a membership needs somebody to belong to")
        expires_raw = payload.get("expires_at")
        try:
            membership = platform.users.grant(
                home_id,
                subject,
                _role_or_400(payload.get("role")),
                actor=principal.subject,
                actor_role=principal.role,
                reason=reason,
                display_name=payload.get("display_name"),
                expires_at=datetime.fromisoformat(expires_raw) if expires_raw else None,
            )
        except MembershipRefused as exc:
            raise forbidden(exc.reason_code, exc.detail) from exc
        return membership.as_view(datetime.now(tz=UTC))

    @app.post("/v1/homes/{home_id}/users/{membership_id}/role", tags=["users"])
    async def change_membership_role(
        home_id: str,
        membership_id: UUID,
        principal: PrincipalDep,
        locale: LocaleDep,
        payload: Annotated[dict[str, Any], Body()],
    ) -> dict[str, Any]:
        check_users(home_id, principal)
        reason = _required_reason(payload)
        _membership_or_404(home_id, membership_id)
        try:
            membership = platform.users.change_role(
                home_id,
                membership_id,
                _role_or_400(payload.get("role")),
                actor=principal.subject,
                actor_role=principal.role,
                reason=reason,
            )
        except MembershipRefused as exc:
            raise forbidden(exc.reason_code, exc.detail) from exc
        return membership.as_view(datetime.now(tz=UTC))

    @app.post("/v1/homes/{home_id}/users/{membership_id}/revoke", tags=["users"])
    async def revoke_membership(
        home_id: str,
        membership_id: UUID,
        principal: PrincipalDep,
        locale: LocaleDep,
        payload: Annotated[dict[str, Any], Body()],
    ) -> dict[str, Any]:
        check_users(home_id, principal)
        reason = _required_reason(payload)
        _membership_or_404(home_id, membership_id)
        try:
            membership = platform.users.revoke(
                home_id,
                membership_id,
                actor=principal.subject,
                actor_role=principal.role,
                reason=reason,
            )
        except MembershipRefused as exc:
            raise forbidden(exc.reason_code, exc.detail) from exc

        # Revoking a membership must revoke the credential with it. A panel
        # whose row says "access taken away" while its token still opens the
        # API is a console that lies about the one thing it is for — and the
        # same is true of a support session somebody thought they had ended.
        revoked_tokens = app.state.tokens.revoke_subject(membership.subject)
        view = membership.as_view(datetime.now(tz=UTC))
        view["tokens_revoked"] = revoked_tokens
        return view

    # ── manual control (spec §0 rule 5) ──

    @app.post("/v1/homes/{home_id}/devices/{device_id}/{capability}", tags=["home"])
    async def operate_device(
        home_id: str,
        device_id: str,
        capability: str,
        principal: PrincipalDep,
        locale: LocaleDep,
        payload: Annotated[dict[str, Any], Body()],
    ) -> dict[str, Any]:
        """A person operating a device directly.

        This did not exist. The policy chain had a manual-override rule, the
        translations had reason codes for it, and `record_manual_change` was
        called by two tests and nothing else — so §0 rule 5 held for somebody
        flipping a physical switch, which Home Assistant reports, and had no
        path at all through SYLTRA's own surfaces. The console could approve a
        recommendation and could not turn on a light.

        The permission required comes from the capability's declared safety
        class, so a wall panel reaches comfort and stops at a lock without any
        list of allowed capabilities existing anywhere.
        """
        check_read(home_id, principal)
        try:
            needed = permission_for_capability(capability)
        except KeyError as exc:
            raise not_found("UNKNOWN_CAPABILITY", f"no capability {capability}") from exc
        if not principal.may(needed):
            raise forbidden(
                "NOT_ALLOWED_HERE",
                f"{principal.role.value} may not operate {capability}",
            )
        if "value" not in payload:
            raise bad_request("VALUE_REQUIRED", "say what to set it to")

        try:
            decision = platform.policy.authorize_manual_control(
                home_id,
                device_id,
                capability,
                payload["value"],
                actor=principal.subject,
            )
        except ValueError as exc:
            raise forbidden("NOT_OPERABLE_BY_HAND", str(exc)) from exc

        request = build_manual_action(decision, device_id, capability, payload["value"])
        try:
            result = await platform.orchestrator.execute(request)
        except ActionRefused as exc:
            raise conflict(exc.reason_code, str(exc)) from exc
        return {
            "device_id": device_id,
            "capability": capability,
            "status": result.status.value,
            "verified": result.verified,
            "reason_codes": result.reason_codes,
            "reasons": translate_reasons(result.reason_codes, locale),
        }

    # ── wall panels (owner decision, 2026-08-21) ──

    #: A panel's token lives as long as the panel is on the wall. Unlike a
    #: guest or a support session, there is no visit for it to outlast — what
    #: ends it is the owner taking it down, from the console.
    PANEL_TTL = timedelta(days=3650)

    @app.get("/v1/homes/{home_id}/panels", tags=["panels"])
    async def list_panels(
        home_id: str, principal: PrincipalDep, locale: LocaleDep
    ) -> dict[str, Any]:
        check_read(home_id, principal)
        now = datetime.now(tz=UTC)
        return {
            "home_id": home_id,
            "panels": [
                membership.as_view(now)
                for membership in platform.users.members(home_id, now)
                if membership.role is Role.PANEL
            ],
            "may_manage": principal.may(Permission.MANAGE_USERS),
        }

    @app.post("/v1/homes/{home_id}/panels", tags=["panels"])
    async def register_panel(
        home_id: str,
        principal: PrincipalDep,
        locale: LocaleDep,
        payload: Annotated[dict[str, Any], Body()],
    ) -> dict[str, Any]:
        """Register a wall panel and hand back its token, once.

        Named by where it hangs rather than by a person, because that is what
        the audit trail will have to say: "the hall panel" is checkable and
        "somebody" is not.

        The token is returned in this response and never again — the same rule
        every other token in this platform follows, and the reason a lost panel
        is re-registered rather than looked up.
        """
        check_users(home_id, principal)
        reason = _required_reason(payload)
        location = str(payload.get("location", "")).strip()
        if not location:
            raise bad_request(
                "LOCATION_REQUIRED",
                "a panel is named by where it hangs; the audit trail will need it",
            )

        try:
            membership = platform.users.grant(
                home_id,
                subject=f"panel:{location}",
                role=Role.PANEL,
                actor=principal.subject,
                actor_role=principal.role,
                reason=reason,
                display_name=location,
                # Explicit, so the directory's expiring-role defaults do not
                # quietly give a wall panel a guest's twenty-four hours.
                expires_at=datetime.now(tz=UTC) + PANEL_TTL,
            )
        except MembershipRefused as exc:
            raise forbidden(exc.reason_code, exc.detail) from exc

        token, _ = app.state.tokens.issue(
            subject=f"panel:{location}",
            role=Role.PANEL,
            home_ids={home_id},
            ttl=PANEL_TTL,
            display_name=location,
        )
        view = membership.as_view(datetime.now(tz=UTC))
        # Shown once. A panel that lost its token is re-registered, not
        # recovered — which is also what makes revoking one meaningful.
        view["token"] = token
        view["token_shown_once"] = True
        return view

    # ── audit ──

    @app.get("/v1/audit", tags=["audit"])
    async def audit(
        principal: PrincipalDep,
        locale: LocaleDep,
        home_id: Annotated[str, Query(description="Home to read the audit trail for")],
        limit: Annotated[int, Query(ge=1, le=200)] = 50,
        offset: Annotated[int, Query(ge=0)] = 0,
    ) -> dict[str, Any]:
        check_audit(home_id, principal)
        entries: list[dict[str, Any]] = []
        for entry in platform.policy.audit:
            if entry.get("home_id") == home_id:
                # Every other endpoint translates its reason codes. This one
                # did not, so the audit trail — the screen most likely to be
                # read after something went wrong — was the one place a
                # household saw `AUTOMATION_NOT_YET_TRUSTED` instead of words.
                entries.append(
                    {
                        "source": "policy",
                        **entry,
                        "reasons": translate_reasons(entry.get("reason_codes", []), locale),
                    }
                )
        # `detail` carries what the entry was *about* — the device, the
        # capability, the value, the safety class. Dropping it left the audit
        # trail able to say that something was dispatched but not to what,
        # which UI guidelines §17.14 lists as a required field and an incident
        # review would need first.
        for action_entry in platform.orchestrator.audit:
            if action_entry.home_id == home_id:
                entries.append(
                    {
                        "source": "action",
                        "occurred_at": action_entry.occurred_at.isoformat(),
                        "action": action_entry.action,
                        "actor": action_entry.actor,
                        "reason": action_entry.reason,
                        **action_entry.detail,
                    }
                )
        for risk_entry in platform.risk.audit:
            if risk_entry.home_id == home_id:
                entries.append(
                    {
                        "source": "risk",
                        "occurred_at": risk_entry.occurred_at.isoformat(),
                        "action": risk_entry.action,
                        "actor": risk_entry.actor,
                        "reason": risk_entry.reason,
                        **risk_entry.detail,
                    }
                )
        entries.sort(key=lambda e: str(e.get("occurred_at", "")), reverse=True)
        return {"home_id": home_id, **_paginate(entries, limit, offset)}

    # ── streaming ──

    @app.websocket("/v1/stream")
    async def stream(websocket: WebSocket) -> None:
        """Authenticated live stream (spec §14.9).

        The token arrives as a query parameter because browsers cannot set
        headers on a WebSocket handshake; it is verified before the socket is
        accepted, so an unauthenticated peer never reaches an open connection.
        """
        token = websocket.query_params.get("token", "")
        home_id = websocket.query_params.get("home_id", "")
        store: TokenStore = websocket.app.state.tokens
        try:
            principal = store.verify(token)
        except Exception:  # noqa: BLE001 - any failure closes before accepting
            await websocket.close(code=4401)
            return
        if not principal.sees(home_id) or not principal.may(Permission.READ_HOME):
            await websocket.close(code=4403)
            return

        # The cursor a reconnecting client last saw. Absent or unparseable is
        # treated as "no history", which resyncs rather than guessing.
        try:
            cursor = int(websocket.query_params.get("cursor", "0"))
        except ValueError:
            cursor = 0

        hub = platform.stream
        await websocket.accept()
        metrics.STREAM_CONNECTIONS.inc()
        queue = hub.subscribe(home_id)
        try:
            missed, resync = hub.missed(home_id, cursor)
            await websocket.send_json(
                {
                    "type": "connected",
                    "home_id": home_id,
                    "subject": principal.subject,
                    "seq": hub.latest_sequence(home_id),
                    # The client re-reads on either. `resync` says so
                    # explicitly, because "I cannot tell you what you missed"
                    # and "you missed nothing" must not look the same.
                    "resync": resync,
                    "missed": [change.as_json() for change in missed],
                    "heartbeat_seconds": HEARTBEAT_SECONDS,
                    "at": datetime.now(tz=UTC).isoformat(),
                }
            )

            # Reading and writing at once: the socket must notice a client that
            # went away, and the client must notice a server that did.
            reader = asyncio.create_task(websocket.receive_text())
            try:
                while True:
                    waiter = asyncio.create_task(queue.get())
                    done, _ = await asyncio.wait(
                        {reader, waiter},
                        timeout=HEARTBEAT_SECONDS,
                        return_when=asyncio.FIRST_COMPLETED,
                    )
                    if reader in done:
                        # Any inbound message is a liveness check; the stream is
                        # one-directional by design and accepts no commands.
                        reader.exception() or reader.result()
                        waiter.cancel()
                        await websocket.send_json(
                            {"type": "pong", "seq": hub.latest_sequence(home_id)}
                        )
                        reader = asyncio.create_task(websocket.receive_text())
                        continue
                    if waiter in done:
                        change = waiter.result()
                        # Coalesce a burst into one notification rather than
                        # making the console re-read once per event.
                        reasons = list(change.reasons)
                        while not queue.empty():
                            reasons.extend(queue.get_nowait().reasons)
                        payload = change.as_json()
                        payload["seq"] = hub.latest_sequence(home_id)
                        payload["reasons"] = sorted(set(reasons))
                        await websocket.send_json(payload)
                        continue
                    waiter.cancel()
                    await websocket.send_json(
                        {
                            "type": "heartbeat",
                            "seq": hub.latest_sequence(home_id),
                            "at": datetime.now(tz=UTC).isoformat(),
                        }
                    )
            finally:
                reader.cancel()
        except WebSocketDisconnect:
            return
        finally:
            hub.unsubscribe(home_id, queue)
            metrics.STREAM_CONNECTIONS.dec()

    # ── view helpers ──

    def _decision_view(decision: Any, locale: str, correlation: str) -> dict[str, Any]:
        return {
            "decision_id": str(decision.decision_id),
            "decision": decision.decision.value,
            "safety_class": decision.safety_class.value,
            "evaluated_at": decision.evaluated_at.isoformat(),
            "expires_at": decision.expires_at.isoformat(),
            "reason_codes": decision.reason_codes,
            "reasons": translate_reasons(decision.reason_codes, locale),
            "correlation_id": correlation,
        }

    def _response_plan_view(case: Any) -> dict[str, Any] | None:
        """What a confirmed hazard authorizes, if anything.

        Advisory cases have no plan: only a confirmation authorizes a response.
        Nothing here can act — the planner cannot reach a device — so this is a
        description a person reads, not a control they press.
        """
        if case.is_advisory:
            return None
        plan = platform.risk.response_plan(case.home_id, case.category, case.room_id)
        if plan is None:
            return None
        return {
            "response": plan.response,
            "notifications": [
                {"capability": step.capability, "detail": step.detail}
                for step in plan.notifications
            ],
            "prepared": [
                {
                    "capability": step.capability,
                    "intended_value": step.intended_value,
                    "device_id": step.device_id,
                    "reachable": step.reachable,
                    "detail": step.detail,
                }
                for step in plan.prepared
            ],
            # Isolations are listed apart from prepared steps because they mean
            # the opposite thing: prepared is "ready, waiting for a person",
            # isolating is "this supply is being cut". Flattening the two would
            # let a screen show a gas shutoff as though it were still pending.
            "isolating": [
                {
                    "capability": step.capability,
                    "intended_value": step.intended_value,
                    "device_id": step.device_id,
                    "reachable": step.reachable,
                    "detail": step.detail,
                    "carried_out": platform.risk.isolation_carried_out(
                        case.home_id, case.category, case.room_id, step.capability
                    ),
                }
                for step in plan.isolating
            ],
            "blocked": [
                {
                    "capability": item.capability,
                    "intended_value": item.intended_value,
                    "reason": item.reason,
                }
                for item in plan.blocked
            ],
            # True only when something actually carried an isolation out. A
            # plan that names a shutoff nobody performed must not read as one
            # that happened.
            "dispatched": any(
                platform.risk.isolation_carried_out(
                    case.home_id, case.category, case.room_id, step.capability
                )
                for step in plan.isolating
            ),
        }

    def _risk_view(case: Any, locale: str) -> dict[str, Any]:
        return {
            "response_plan": _response_plan_view(case),
            "case_id": str(case.case_id),
            "category": case.category.value,
            "state": case.state.value,
            "severity": case.severity.value,
            "confidence": case.confidence,
            "room_id": case.room_id,
            "opened_at": case.opened_at.isoformat(),
            "advisory": case.is_advisory,
            "confirmed_by": case.confirmed_by,
            "reason_codes": case.reason_codes,
            "reasons": translate_reasons(case.reason_codes, locale),
            "evidence": [
                {
                    "origin": item.origin.value,
                    "capability": item.capability,
                    "device_id": item.device_id,
                    "value": item.value,
                    "status": item.status,
                }
                for item in case.evidence
            ],
        }

    return app


def _pending_decision(policy: PolicyService, home_id: str, recommendation_id: UUID) -> Any:
    """Find the approval request a user is answering."""
    for decision in reversed(list(policy.decisions.values())):
        if (
            decision.home_id == home_id
            and decision.recommendation_id == recommendation_id
            and decision.decision is PolicyOutcome.REQUIRE_USER_APPROVAL
        ):
            return decision
    raise not_found("NO_PENDING_APPROVAL", "no approval request for this recommendation")


__all__ = ["API_VERSION", "StateStatus", "create_app"]
