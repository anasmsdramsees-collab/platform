"""Action Orchestrator (spec §14.7).

The only component that commands a device, and the last place a mistake can be
caught before it becomes physical. Spec §14.7 lists what no action may execute
without, and each is checked here immediately before dispatch — not trusted
from earlier in the pipeline, because the gap between authorization and
execution is exactly where state changes.

The dispatch sequence:

1. **Refuse without a live ALLOW.** The decision is re-fetched and re-checked
   at dispatch time (safety invariant 2), not taken on faith from the caller.
2. **Refuse an expired action** (invariant 3).
3. **Deduplicate by idempotency key** (invariant 10) — a redelivered request
   returns the original result rather than acting twice.
4. **Re-check current state.** If the device is already where we want it, or a
   person moved it since the decision, dispatch is abandoned (invariant 5).
5. **Dispatch through the gateway**, never through vendor APIs directly.
6. **Verify the expected state transition.** An action is not successful
   because the call returned; it is successful because the device reports what
   we asked for.
7. **Retry only transient failures**, within `max_attempts`.
8. **Compensate where valid** — restore the previous value if verification
   fails and the capability is reversible.

Every attempt and outcome is recorded immutably (invariant 12).
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from enum import StrEnum
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from syltra_contracts import (
    ActionAttempt,
    ActionRequest,
    ActionResult,
    ActionStatus,
    ActionTarget,
    CapabilityCommand,
    ExpectedState,
    FailureKind,
    PolicyDecision,
    Recommendation,
    SafetyClass,
    derive_idempotency_key,
)
from syltra_contracts.capability_definitions import get_definition

logger = logging.getLogger(__name__)

DEFAULT_ACTION_TTL_SECONDS = 300.0

StateReader = Callable[[str, str], Awaitable[Any]]
"""(device_id, capability) -> current value, or None if unknown."""


class ActionRefused(Exception):
    """Dispatch was refused before anything reached a device."""

    def __init__(self, reason_code: str, detail: str) -> None:
        super().__init__(detail)
        self.reason_code = reason_code


AuditSink = Callable[["AuditEntry"], None]
"""Durable audit writer. Raising signals that the record cannot be stored."""


class DispatchMode(StrEnum):
    """Whether this hub is allowed to command anything at all.

    `OBSERVE_ONLY` is for the first run in a real home. Everything else the
    platform does still happens — events arrive, the twin projects, contexts
    resolve, models train, policy decides, automations evaluate — and nothing
    reaches a device. Every refusal is recorded with the command that was not
    sent, so a week in this mode answers the question a pilot exists to ask:
    *what would SYLTRA have done in this house?*

    This is deliberately not the same thing as OBSERVE on the learning ladder.
    That governs whether the Adaptive Engine proposes; this governs whether
    anything at all is dispatched, including a user-authored automation and a
    deterministic safety response. It is the switch you can hand to a household
    and describe in one sentence.
    """

    ENABLED = "ENABLED"
    OBSERVE_ONLY = "OBSERVE_ONLY"


@dataclass
class OrchestratorConfig:
    environment: str = "development"
    dispatch: DispatchMode = DispatchMode.ENABLED
    """Set to OBSERVE_ONLY for a first pilot: nothing reaches a device."""
    verify_delay_seconds: float = 0.05
    """Pause before reading back state, so the device can settle."""
    compensate_on_failure: bool = True
    require_durable_audit: bool = True
    """Safety invariant 9: when the audit store is unreachable, adaptive
    execution must stop rather than proceed untraceably.

    Set False only where no durable sink is configured at all (development,
    tests) — the orchestrator then keeps its in-memory trail and says so.
    """


@dataclass
class _Record:
    result: ActionResult
    request: ActionRequest


@dataclass
class AuditEntry:
    occurred_at: datetime
    home_id: str
    action: str
    actor: str
    reason: str
    detail: dict[str, Any] = field(default_factory=dict)


def build_action_request(
    decision: PolicyDecision,
    recommendation: Recommendation,
    now: datetime,
    previous_value: Any = None,
    ttl_seconds: float = DEFAULT_ACTION_TTL_SECONDS,
    sequence: int = 1,
) -> ActionRequest:
    """Construct an action from an authorized decision.

    Takes the decision as an argument rather than an id, so there is no way to
    build an action without holding an actual decision object.
    """
    from datetime import timedelta

    capability = recommendation.target.capability
    definition = get_definition(capability)
    return ActionRequest(
        action_id=uuid4(),
        idempotency_key=derive_idempotency_key(
            recommendation.home_id, decision.decision_id, capability, sequence
        ),
        decision_id=decision.decision_id,
        home_id=recommendation.home_id,
        correlation_id=recommendation.recommendation_id,
        target=ActionTarget(
            device_id=recommendation.target.device_id,
            capability=capability,
            room_id=recommendation.target.room_id,
        ),
        value=recommendation.proposed_value,
        expected_state=ExpectedState(
            capability=capability, operator="equals", value=recommendation.proposed_value
        ),
        safety_class=decision.safety_class,
        created_at=now,
        expires_at=now + timedelta(seconds=ttl_seconds),
        reversible=definition.reversible,
        previous_value=previous_value,
        metadata={"recommendation_type": recommendation.recommendation_type},
    )


class ActionOrchestrator:
    def __init__(
        self,
        gateway: Any,
        read_state: StateReader,
        get_decision: Callable[[UUID], PolicyDecision | None],
        config: OrchestratorConfig | None = None,
        audit_sink: AuditSink | None = None,
    ) -> None:
        self._gateway = gateway
        self._read_state = read_state
        self._get_decision = get_decision
        self._config = config or OrchestratorConfig()
        self._audit_sink = audit_sink
        self.audit_store_available = True
        self._by_key: dict[str, _Record] = {}
        self._pending: dict[str, ActionRequest] = {}
        self._cancelled: set[str] = set()
        self.audit: list[AuditEntry] = []

    # ── queries ──

    def result_for(self, idempotency_key: str) -> ActionResult | None:
        record = self._by_key.get(idempotency_key)
        return record.result if record else None

    def results(self, home_id: str | None = None) -> list[ActionResult]:
        found = [r.result for r in self._by_key.values()]
        if home_id is not None:
            found = [r for r in found if r.home_id == home_id]
        return sorted(found, key=lambda r: r.completed_at)

    # ── manual override ──

    def register_pending(self, request: ActionRequest, now: datetime | None = None) -> None:
        """Declare an action as intended before it is dispatched.

        Without this the orchestrator learns of an action only when `execute`
        runs, leaving no window in which a manual change could cancel it. A
        caller that builds a request and dispatches later should register it so
        `cancel_conflicting` can find it in flight (safety invariant 5).
        """
        if request.idempotency_key in self._by_key:
            return
        moment = now or datetime.now(tz=UTC)
        self._pending[request.idempotency_key] = request
        self._audit(
            request.home_id,
            "ACTION_REQUESTED",
            actor="action-orchestrator",
            reason="action registered pending dispatch",
            detail={
                "action_id": str(request.action_id),
                "capability": request.target.capability,
                "device_id": request.target.device_id,
                "registered_at": moment.isoformat(),
            },
        )

    def pending_keys(self) -> list[str]:
        return sorted(self._pending)

    def cancel_conflicting(self, home_id: str, device_id: str, capability: str) -> list[str]:
        """Cancel pending actions a person's manual control has superseded.

        Safety invariant 5. Called when a manual change is observed; any action
        still in flight for that device and capability is marked cancelled so it
        cannot land after the person has already set what they wanted.
        """
        cancelled: list[str] = []
        for key, request in list(self._pending.items()):
            if (
                request.home_id == home_id
                and request.target.device_id == device_id
                and request.target.capability == capability
            ):
                self._cancelled.add(key)
                self._pending.pop(key, None)
                cancelled.append(key)
        if cancelled:
            self._audit(
                home_id,
                "ACTION_CANCELLED_BY_MANUAL_OVERRIDE",
                actor="occupant",
                reason="manual control supersedes pending adaptive action",
                detail={"cancelled_keys": cancelled, "device_id": device_id},
            )
        return cancelled

    # ── dispatch ──

    async def execute(self, request: ActionRequest, now: datetime | None = None) -> ActionResult:
        """Execute one authorized action, verifying the outcome.

        ``now`` pins the clock for the whole call. Mixing an injected instant
        with wall-clock reads would let preflight and the retry loop disagree
        about the current time — the sort of split that makes a TTL check pass
        in one place and fail in another.
        """
        clock: Callable[[], datetime] = (
            (lambda: now) if now is not None else (lambda: datetime.now(tz=UTC))
        )
        moment = clock()

        # Idempotency (safety invariant 10): the same intent, once.
        existing = self._by_key.get(request.idempotency_key)
        if existing is not None:
            self._audit(
                request.home_id,
                "ACTION_DEDUPLICATED",
                actor="action-orchestrator",
                reason="idempotency key already executed",
                detail={"idempotency_key": request.idempotency_key},
            )
            return existing.result

        try:
            self._preflight(request, moment)
        except ActionRefused as refusal:
            return self._finalize(
                request,
                ActionStatus.CANCELLED
                if refusal.reason_code.startswith("MANUAL")
                else ActionStatus.EXPIRED
                if "EXPIRED" in refusal.reason_code
                else ActionStatus.FAILED,
                [refusal.reason_code],
                moment,
                attempts=[],
            )

        current = await self._read_state(request.target.device_id, request.target.capability)
        if request.expected_state.is_satisfied_by(current):
            return self._finalize(
                request, ActionStatus.SUCCEEDED, ["ALREADY_IN_EXPECTED_STATE"], moment,
                attempts=[], observed=current,
            )

        attempts: list[ActionAttempt] = []
        observed: Any = current
        for attempt_number in range(1, request.max_attempts + 1):
            if request.idempotency_key in self._cancelled:
                return self._finalize(
                    request, ActionStatus.CANCELLED, ["MANUAL_OVERRIDE_DETECTED"], moment,
                    attempts, observed,
                )
            if request.is_expired_at(clock()):
                return self._finalize(
                    request, ActionStatus.EXPIRED, ["ACTION_EXPIRED_BEFORE_DISPATCH"],
                    moment, attempts, observed,
                )

            started = clock()
            attempt, observed = await self._attempt(request, attempt_number, started, clock)
            attempts.append(attempt)

            if attempt.verified:
                return self._finalize(
                    request, ActionStatus.SUCCEEDED, ["VERIFIED"], moment, attempts, observed
                )
            if attempt.failure_kind is not None and not attempt.failure_kind.retryable:
                # A permanent failure repeated is still a permanent failure.
                break

        result = self._finalize(
            request, ActionStatus.FAILED, ["VERIFICATION_FAILED"], moment, attempts, observed
        )
        if self._config.compensate_on_failure:
            await self._compensate(request, observed)
        return result

    async def _attempt(
        self,
        request: ActionRequest,
        number: int,
        started: datetime,
        clock: Callable[[], datetime],
    ) -> tuple[ActionAttempt, Any]:
        try:
            outcome = await self._gateway.execute_capability_command(
                CapabilityCommand(
                    device_id=request.target.device_id,
                    capability=request.target.capability,
                    value=request.value,
                    correlation_id=str(request.correlation_id),
                )
            )
        except Exception as exc:  # noqa: BLE001 - any transport error is transient
            logger.warning("action dispatch attempt %d raised: %s", number, exc)
            return (
                ActionAttempt(
                    attempt=number,
                    started_at=started,
                    finished_at=clock(),
                    dispatched=False,
                    verified=False,
                    failure_kind=FailureKind.TRANSIENT,
                    reason=f"dispatch error: {exc.__class__.__name__}",
                ),
                None,
            )

        if not outcome.accepted:
            # A refusal is the gateway's considered answer; retrying it would
            # just re-send a command the integration already declined.
            return (
                ActionAttempt(
                    attempt=number,
                    started_at=started,
                    finished_at=clock(),
                    dispatched=False,
                    verified=False,
                    failure_kind=FailureKind.PERMANENT,
                    reason=outcome.reason or "gateway refused the command",
                ),
                None,
            )

        await asyncio.sleep(self._config.verify_delay_seconds)
        observed = await self._read_state(request.target.device_id, request.target.capability)
        verified = request.expected_state.is_satisfied_by(observed)
        return (
            ActionAttempt(
                attempt=number,
                started_at=started,
                finished_at=clock(),
                dispatched=True,
                verified=verified,
                failure_kind=None if verified else FailureKind.TRANSIENT,
                reason=None if verified else f"device reported {observed!r}",
            ),
            observed,
        )

    @property
    def dispatch_enabled(self) -> bool:
        """Whether this orchestrator may command a device."""
        return self._config.dispatch is DispatchMode.ENABLED

    def _preflight(self, request: ActionRequest, now: datetime) -> None:
        """The spec §14.7 preconditions, checked at dispatch time."""
        # First, before anything else and regardless of class, decision or
        # urgency: an observing hub does not command. Placed at the top of the
        # one function every dispatch passes through, so there is no path that
        # reaches a device without meeting it — including a confirmed safety
        # response, which is the case most likely to argue for an exception and
        # the one where an exception would be least defensible in a stranger's
        # home.
        if self._config.dispatch is DispatchMode.OBSERVE_ONLY:
            raise ActionRefused(
                "DISPATCH_DISABLED_OBSERVE_ONLY",
                f"this hub is observing only; {request.target.capability} was not sent",
            )

        if request.is_expired_at(now):
            raise ActionRefused("ACTION_EXPIRED", "action TTL elapsed before dispatch")

        decision = self._get_decision(request.decision_id)
        if decision is None:
            raise ActionRefused(
                "NO_POLICY_DECISION", f"decision {request.decision_id} is not on record"
            )
        if not decision.authorizes_execution_at(now):
            raise ActionRefused(
                "POLICY_DECISION_NOT_AUTHORIZING",
                f"decision is {decision.decision.value}"
                + (" and expired" if decision.is_expired_at(now) else ""),
            )
        if decision.home_id != request.home_id:
            raise ActionRefused(
                "DECISION_HOME_MISMATCH",
                "the decision authorizes a different household",
            )

        # Safety invariant 16: development and simulation block real critical
        # actuators, regardless of what policy said.
        definition = get_definition(request.target.capability)
        if self._config.environment in {
            "development",
            "simulation",
        } and definition.safety_class in {
            SafetyClass.LIFE_SAFETY_CRITICAL,
            SafetyClass.SAFETY_RELATED,
        }:
            raise ActionRefused(
                "CRITICAL_ACTUATOR_BLOCKED_IN_DEVELOPMENT",
                f"{request.target.capability} is blocked in {self._config.environment}",
            )
        if request.idempotency_key in self._cancelled:
            raise ActionRefused("MANUAL_OVERRIDE_DETECTED", "superseded by manual control")

        # Safety invariant 9: loss of the database must fail safely and prevent
        # untraceable adaptive execution. An adaptive action that cannot be
        # recorded does not run. A deterministic safety response still may —
        # refusing to act on a confirmed hazard because a log is down would be
        # the more dangerous failure.
        if (
            self._config.require_durable_audit
            and self._audit_sink is not None
            and not self.audit_store_available
            and request.origin != "safety"
        ):
            raise ActionRefused(
                "AUDIT_STORE_UNAVAILABLE",
                "adaptive actions cannot execute while the audit trail cannot be written",
            )

    async def _compensate(self, request: ActionRequest, observed: Any) -> None:
        """Restore the previous value where the capability supports it."""
        if not request.reversible or request.previous_value is None:
            return
        try:
            await self._gateway.execute_capability_command(
                CapabilityCommand(
                    device_id=request.target.device_id,
                    capability=request.target.capability,
                    value=request.previous_value,
                    correlation_id=str(request.correlation_id),
                )
            )
        except Exception:  # noqa: BLE001 - compensation is best effort
            logger.exception("compensating action failed for %s", request.action_id)
            return
        record = self._by_key.get(request.idempotency_key)
        if record is not None:
            self._by_key[request.idempotency_key] = _Record(
                result=record.result.model_copy(update={"compensated": True}),
                request=request,
            )
        self._audit(
            request.home_id,
            "ACTION_COMPENSATED",
            actor="action-orchestrator",
            reason="verification failed; restored previous value",
            detail={"restored_to": request.previous_value, "observed": observed},
        )

    def _finalize(
        self,
        request: ActionRequest,
        status: ActionStatus,
        reason_codes: list[str],
        now: datetime,
        attempts: list[ActionAttempt],
        observed: Any = None,
    ) -> ActionResult:
        result = ActionResult(
            action_id=request.action_id,
            idempotency_key=request.idempotency_key,
            decision_id=request.decision_id,
            home_id=request.home_id,
            correlation_id=request.correlation_id,
            status=status,
            attempts=attempts,
            reason_codes=reason_codes,
            observed_value=observed,
            completed_at=now,
        )
        self._by_key[request.idempotency_key] = _Record(result=result, request=request)
        self._pending.pop(request.idempotency_key, None)
        self._audit(
            request.home_id,
            f"ACTION_{status.value}",
            actor="action-orchestrator",
            reason=",".join(reason_codes),
            detail={
                "action_id": str(request.action_id),
                "capability": request.target.capability,
                "device_id": request.target.device_id,
                "value": request.value,
                "attempts": len(attempts),
                "safety_class": request.safety_class.value,
            },
        )
        return result

    def _audit(
        self,
        home_id: str,
        action: str,
        actor: str,
        reason: str,
        detail: dict[str, Any] | None = None,
    ) -> None:
        entry = AuditEntry(
            occurred_at=datetime.now(tz=UTC),
            home_id=home_id,
            action=action,
            actor=actor,
            reason=reason,
            detail=detail or {},
        )
        self.audit.append(entry)
        if self._audit_sink is None:
            return
        try:
            self._audit_sink(entry)
        except Exception:  # noqa: BLE001 - any sink failure means "not durable"
            # Recorded rather than raised: the action already happened, and
            # losing the record must not also lose the outcome. The flag stops
            # the *next* adaptive action instead.
            self.audit_store_available = False
            logger.exception("audit sink unavailable; adaptive execution will be blocked")
        else:
            self.audit_store_available = True
