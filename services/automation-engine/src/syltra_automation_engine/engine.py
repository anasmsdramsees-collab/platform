"""Deterministic evaluation of user-authored automations (spec §2.3, ADR-009).

What this module is allowed to do: read the twin, read the active contexts, and
decide that an automation *should* act. What it cannot do is act. It holds no
gateway, builds no command, and calls nothing that sends — a proposal goes to
the Policy and Safety Service exactly as an adaptive recommendation does, and
policy decides.

The module imports nothing from the Adaptive Engine, no model runtime and no
dataframe library. Safety invariant 7 requires fixed automations to keep
working when every model is suspended, and a test runs a fresh interpreter to
prove the import graph stays clean.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from syltra_contracts.automations import (
    Automation,
    AutomationAction,
    AutomationCondition,
    ConditionKind,
    TriggerKind,
)
from syltra_digital_twin.core import HomeState

# How long after an automation acts its own echo is ignored. A thermostat
# reporting the value SYLTRA just set is not a reason to set it again.
ECHO_WINDOW = timedelta(seconds=90)


@dataclass(frozen=True)
class AutomationProposal:
    """An automation asking for something. Not a command.

    Deliberately shaped like a recommendation rather than an action: it names
    what and why, carries an expiry, and has no field that could carry a
    dispatch result. The next thing that touches it is policy.
    """

    automation_id: Any
    home_id: str
    name: str
    action: AutomationAction
    triggered_at: datetime
    expires_at: datetime
    reason_codes: tuple[str, ...]

    def is_expired_at(self, now: datetime) -> bool:
        return now >= self.expires_at


@dataclass
class _AutomationState:
    """What the engine remembers about one automation, per home."""

    last_fired_at: datetime | None = None
    # Values this automation set, and when. Used to recognise its own echo.
    recent_effects: dict[tuple[str, str], tuple[Any, datetime]] = field(default_factory=dict)


class SkipReason:
    """Why an automation did not fire.

    Named constants rather than free text: these end up in the audit trail and
    on a screen, and "did not fire" is only useful if it says which of a dozen
    reasons applied.
    """

    DISABLED = "AUTOMATION_DISABLED"
    TRIGGER_NOT_MET = "TRIGGER_NOT_MET"
    CONDITION_NOT_MET = "CONDITION_NOT_MET"
    REARMING = "AUTOMATION_REARMING"
    OWN_ECHO = "AUTOMATION_OWN_ECHO"
    MANUAL_OVERRIDE = "MANUAL_OVERRIDE_ACTIVE"
    TARGET_UNKNOWN = "TARGET_STATE_UNKNOWN"


@dataclass(frozen=True)
class Evaluation:
    """The result of one pass: what would run, and what did not and why."""

    proposals: tuple[AutomationProposal, ...] = ()
    skipped: tuple[tuple[Any, str], ...] = ()

    def reason_for(self, automation_id: Any) -> str | None:
        for identifier, reason in self.skipped:
            if identifier == automation_id:
                return reason
        return None


def _reading(home: HomeState, capability: str, device_id: str | None, room_id: str | None) -> Any:
    """The current reading for a capability, preferring an exact device."""
    for device in home.devices.values():
        if capability not in device.capabilities:
            continue
        if device_id is not None and device.device_id != device_id:
            continue
        if device_id is None and room_id is not None and device.room_id != room_id:
            continue
        return device.capabilities[capability]
    return None


def _numeric(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def _condition_holds(
    condition: AutomationCondition,
    home: HomeState,
    active_contexts: frozenset[str],
    now: datetime,
) -> bool:
    if condition.kind is ConditionKind.CONTEXT_ACTIVE:
        return condition.context_type in active_contexts
    if condition.kind is ConditionKind.CONTEXT_INACTIVE:
        return condition.context_type not in active_contexts

    reading = _reading(home, condition.capability or "", condition.device_id, condition.room_id)
    # A condition over a value nobody has reported — or one that has gone stale
    # against its own freshness rule — is not satisfied. Treating unknown as
    # false is the safe direction: an automation should not fire because the
    # platform cannot see a reason not to.
    #
    # `is_usable_for_decisions` is the twin's own predicate, the same one policy
    # and the risk engine use, so an automation cannot act on a value the rest
    # of the platform would refuse.
    if reading is None or not reading.is_usable_for_decisions(now):
        return False

    if condition.kind is ConditionKind.STATE_EQUALS:
        return bool(reading.value == condition.value)

    current = _numeric(reading.value)
    threshold = _numeric(condition.value)
    if current is None or threshold is None:
        return False
    if condition.kind is ConditionKind.THRESHOLD_ABOVE:
        return current > threshold
    return current < threshold


def _trigger_fires(
    automation: Automation,
    home: HomeState,
    started_contexts: frozenset[str],
    now: datetime,
) -> bool:
    trigger = automation.trigger
    if trigger.kind is TriggerKind.CONTEXT_STARTED:
        return trigger.context_type in started_contexts

    reading = _reading(home, trigger.capability or "", trigger.device_id, trigger.room_id)
    if reading is None or not reading.is_usable_for_decisions(now):
        return False

    if trigger.kind is TriggerKind.STATE_EQUALS:
        return bool(reading.value == trigger.value)

    current = _numeric(reading.value)
    threshold = _numeric(trigger.value)
    if current is None or threshold is None:
        return False
    if trigger.kind is TriggerKind.THRESHOLD_ABOVE:
        return current > threshold
    return current < threshold


class AutomationEngine:
    """Evaluates automations. Never dispatches one.

    State kept here is only what determinism needs: when each automation last
    fired, and what it set. Both exist to stop loops, and neither is a cache of
    device state — the twin is the only source of that.
    """

    def __init__(self) -> None:
        self._automations: dict[str, dict[Any, Automation]] = {}
        self._state: dict[str, dict[Any, _AutomationState]] = {}

    # ── the register ──

    def upsert(self, automation: Automation) -> Automation:
        self._automations.setdefault(automation.home_id, {})[automation.automation_id] = automation
        self._state.setdefault(automation.home_id, {}).setdefault(
            automation.automation_id, _AutomationState()
        )
        return automation

    def remove(self, home_id: str, automation_id: Any) -> bool:
        removed = self._automations.get(home_id, {}).pop(automation_id, None) is not None
        self._state.get(home_id, {}).pop(automation_id, None)
        return removed

    def get(self, home_id: str, automation_id: Any) -> Automation | None:
        return self._automations.get(home_id, {}).get(automation_id)

    def list_for(self, home_id: str) -> list[Automation]:
        return sorted(self._automations.get(home_id, {}).values(), key=lambda a: a.name)

    def set_enabled(self, home_id: str, automation_id: Any, enabled: bool) -> Automation | None:
        existing = self.get(home_id, automation_id)
        if existing is None:
            return None
        updated = existing.model_copy(update={"enabled": enabled, "version": existing.version + 1})
        return self.upsert(updated)

    def last_fired(self, home_id: str, automation_id: Any) -> datetime | None:
        return self._state.get(home_id, {}).get(automation_id, _AutomationState()).last_fired_at

    # ── evaluation ──

    def evaluate(
        self,
        home_id: str,
        home: HomeState,
        now: datetime | None = None,
        active_contexts: Iterable[str] = (),
        started_contexts: Iterable[str] = (),
        manual_override: Mapping[tuple[str, str], datetime] | None = None,
        dry_run: bool = False,
    ) -> Evaluation:
        """Decide what should be proposed, and why the rest was not.

        `manual_override` maps (device, capability) to when a person last set it
        themselves. Spec §0 rule 16: manual control always overrides adaptive
        automation, so an automation that would move something a person has just
        moved does not get to.

        `dry_run` evaluates without recording that anything fired — which is
        what a test-mode run in the console needs, and what makes it safe to
        offer one.
        """
        moment = now or datetime.now(tz=UTC)
        active = frozenset(active_contexts)
        started = frozenset(started_contexts)
        overrides = manual_override or {}

        proposals: list[AutomationProposal] = []
        skipped: list[tuple[Any, str]] = []

        for automation in self.list_for(home_id):
            state = self._state[home_id].setdefault(automation.automation_id, _AutomationState())

            if not automation.enabled:
                skipped.append((automation.automation_id, SkipReason.DISABLED))
                continue

            if not _trigger_fires(automation, home, started, moment):
                skipped.append((automation.automation_id, SkipReason.TRIGGER_NOT_MET))
                continue

            if state.last_fired_at is not None and (
                moment - state.last_fired_at
            ) < timedelta(seconds=automation.rearm_seconds):
                skipped.append((automation.automation_id, SkipReason.REARMING))
                continue

            if self._is_own_echo(automation, home, state, moment):
                skipped.append((automation.automation_id, SkipReason.OWN_ECHO))
                continue

            if not all(
                _condition_holds(c, home, active, moment) for c in automation.conditions
            ):
                skipped.append((automation.automation_id, SkipReason.CONDITION_NOT_MET))
                continue

            overridden = self._manually_overridden(automation, overrides, moment)
            if overridden:
                skipped.append((automation.automation_id, SkipReason.MANUAL_OVERRIDE))
                continue

            expiry = moment + _action_ttl()
            for action in automation.actions:
                proposals.append(
                    AutomationProposal(
                        automation_id=automation.automation_id,
                        home_id=home_id,
                        name=automation.name,
                        action=action,
                        triggered_at=moment,
                        expires_at=expiry,
                        reason_codes=("AUTOMATION_TRIGGERED",),
                    )
                )
            if not dry_run:
                state.last_fired_at = moment
                for action in automation.actions:
                    key = (action.device_id or "", action.capability)
                    state.recent_effects[key] = (action.value, moment)

        return Evaluation(proposals=tuple(proposals), skipped=tuple(skipped))

    # ── loop prevention (§14.8) ──

    def _is_own_echo(
        self,
        automation: Automation,
        home: HomeState,
        state: _AutomationState,
        now: datetime,
    ) -> bool:
        """True when the trigger is reading back what this automation just set.

        The direct loop: an automation turns a light on, the light reports it is
        on, and the trigger fires again. The rearm interval bounds it; this
        stops it happening at all, which is the difference between a light that
        flickers on a slow schedule and one that does not.
        """
        trigger = automation.trigger
        if trigger.kind is TriggerKind.CONTEXT_STARTED or not trigger.capability:
            return False
        for (device_id, capability), (value, when) in state.recent_effects.items():
            if capability != trigger.capability:
                continue
            if trigger.device_id is not None and device_id != trigger.device_id:
                continue
            if now - when > ECHO_WINDOW:
                continue
            reading = _reading(home, capability, device_id or None, trigger.room_id)
            if reading is not None and reading.value == value:
                return True
        return False

    def _manually_overridden(
        self,
        automation: Automation,
        overrides: Mapping[tuple[str, str], datetime],
        now: datetime,
    ) -> bool:
        """Spec §0 rule 16: a person's hand wins."""
        for action in automation.actions:
            key = (action.device_id or "", action.capability)
            when = overrides.get(key)
            if when is not None and now - when < ECHO_WINDOW:
                return True
        return False


def _action_ttl() -> timedelta:
    from syltra_contracts.automations import DEFAULT_ACTION_TTL

    return DEFAULT_ACTION_TTL
