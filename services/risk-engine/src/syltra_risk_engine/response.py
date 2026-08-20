"""What a confirmed hazard authorizes, and what it does not (spec §20.4, §20.5).

A confirmation names its response — `NOTIFY_AND_PREPARE_GAS_ISOLATION` — and
until now nothing turned that name into anything. This module turns it into a
**plan**: what would be done, to which device, whether that device can be
reached, and which parts are not this system's to carry out.

The distinction the whole module exists to hold:

- **Notify** is executable. `notification.send` is NON_CRITICAL and requires no
  confirmation; telling a household their gas alarm is sounding operates
  nothing.
- **Prepare** is executable and touches nothing. It resolves the valve, checks
  the twin says it is reachable, and computes the command — so that when a
  person decides, the system already knows what to do and has verified it can.
- **Execute** is not here. Closing a valve, sounding a siren or unlocking egress
  needs explicit product-owner approval under spec §0 rule 9, and no line of
  this module can perform one.

That last point is structural, not a convention. `ResponseStage` has two
members and no third: there is no value a step could carry that would mean
"execute", so no caller can construct one and no future edit can add one
without changing the type and failing the tests that pin it.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from syltra_contracts.capability_definitions import Confirmation, get_definition
from syltra_digital_twin.core import HomeState

from syltra_risk_engine.governor import Confirmation as HazardConfirmation

NOTIFICATION_CAPABILITY = "notification.send"


class ResponseStage(StrEnum):
    """The only two things a confirmed hazard may cause here.

    There is deliberately no `EXECUTE`. Adding one would be the change that
    lets this path command a valve, and it should require editing this enum,
    reading this comment, and breaking
    `test_the_response_path_has_no_execute_stage`.
    """

    NOTIFY = "NOTIFY"
    PREPARE = "PREPARE"


@dataclass(frozen=True)
class ResponseStep:
    """One thing the response does, or would do."""

    stage: ResponseStage
    capability: str
    intended_value: Any
    device_id: str | None = None
    room_id: str | None = None
    reachable: bool = False
    detail: str = ""

    def __post_init__(self) -> None:
        definition = get_definition(self.capability)
        # A NOTIFY step may only ever send a message. Without this, a caller
        # could label a valve command "NOTIFY" and walk it past every check
        # that looks at the stage.
        if self.stage is ResponseStage.NOTIFY and self.capability != NOTIFICATION_CAPABILITY:
            msg = f"a NOTIFY step may only use {NOTIFICATION_CAPABILITY}, not {self.capability}"
            raise ValueError(msg)
        # A PREPARE step targets something that needs a deterministic rule to
        # act. Preparing a light is not a safety response.
        if (
            self.stage is ResponseStage.PREPARE
            and definition.confirmation is not Confirmation.DETERMINISTIC_SAFETY_RULE
        ):
            msg = (
                f"{self.capability} does not require a deterministic safety rule; "
                "preparing it is not a hazard response"
            )
            raise ValueError(msg)


@dataclass(frozen=True)
class BlockedAction:
    """Something the response names that this system will not carry out."""

    capability: str
    intended_value: Any
    reason: str


@dataclass(frozen=True)
class ResponsePlan:
    """Everything a confirmation authorizes, separated by what it costs.

    `blocked` is not an error list. It is the honest half of the plan: the
    response names an action, the platform can identify the device, and it
    still will not act — because doing so needs approval this repository cannot
    grant.
    """

    response: str
    confirmed_by: str
    category: str
    room_id: str | None
    planned_at: datetime
    steps: tuple[ResponseStep, ...] = ()
    blocked: tuple[BlockedAction, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def notifications(self) -> tuple[ResponseStep, ...]:
        return tuple(s for s in self.steps if s.stage is ResponseStage.NOTIFY)

    @property
    def prepared(self) -> tuple[ResponseStep, ...]:
        return tuple(s for s in self.steps if s.stage is ResponseStage.PREPARE)

    @property
    def unreachable(self) -> tuple[ResponseStep, ...]:
        """Prepared steps whose device the twin cannot vouch for.

        Worth surfacing rather than hiding: a prepared isolation that names no
        reachable valve is a plan that will fail at the moment it matters, and
        the household should learn that now rather than then.
        """
        return tuple(s for s in self.prepared if not s.reachable)


# ── what each authorized response consists of ──

# `prepare` names the capability and the value an isolation would set.
# `blocked` names an action the response calls for that this system will not
# perform without approval, and why.
_GAS = {
    "prepare": ("valve.state", "closed"),
    "blocked": (),
}
_WATER = {
    "prepare": ("valve.state", "closed"),
    "blocked": (),
}
_EGRESS = {
    "prepare": None,
    # Unlocking is not preparable: there is no half of it that changes nothing.
    "blocked": (("lock.state", "unlocked", "unlocking egress operates a door"),),
}
_VENTILATE = {
    "prepare": None,
    "blocked": (("switch.power", True, "ventilation operates a device"),),
}

RESPONSE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "NOTIFY_AND_PREPARE_GAS_ISOLATION": _GAS,
    "NOTIFY_AND_PREPARE_WATER_ISOLATION": _WATER,
    "NOTIFY_AND_UNLOCK_EGRESS": _EGRESS,
    "NOTIFY_AND_VENTILATE": _VENTILATE,
}


class UnknownResponse(ValueError):
    """A confirmation named a response with no definition.

    Raised rather than ignored: a confirmed hazard whose response nobody
    defined must not pass silently as "nothing to do".
    """


def _find_device(home: HomeState | None, capability: str, room_id: str | None) -> tuple[str | None, bool]:
    """The device that offers this capability, preferring the affected room."""
    if home is None:
        return None, False
    candidates = []
    for device in home.devices.values():
        if capability in device.capabilities:
            candidates.append(device)
    if not candidates:
        return None, False
    # A hazard in the kitchen should prepare the kitchen's valve if there is
    # one, and the home's main valve otherwise.
    in_room = [d for d in candidates if room_id is not None and d.room_id == room_id]
    chosen = (in_room or candidates)[0]
    reading = chosen.capabilities.get(capability)
    reachable = bool(reading is not None and getattr(reading, "status", None) != "UNKNOWN")
    return chosen.device_id, reachable


def plan_response(
    confirmation: HazardConfirmation,
    home: HomeState | None = None,
    now: datetime | None = None,
) -> ResponsePlan:
    """Turn a confirmation's authorized response into a concrete plan.

    Never dispatches, and cannot: the only stages it can produce are NOTIFY and
    PREPARE, and neither reaches a gateway from here. Handing the plan to
    something that *can* dispatch is a separate, deliberate act — and for the
    prepared steps, one that needs approval under spec §0 rule 9.
    """
    response = confirmation.authorized_response
    definition = RESPONSE_DEFINITIONS.get(response)
    if definition is None:
        msg = f"no response definition for {response!r}"
        raise UnknownResponse(msg)

    moment = now or datetime.now(tz=UTC)
    steps: list[ResponseStep] = [
        ResponseStep(
            stage=ResponseStage.NOTIFY,
            capability=NOTIFICATION_CAPABILITY,
            intended_value=response,
            room_id=confirmation.room_id,
            reachable=True,
            detail="the household is told what was confirmed and where",
        )
    ]

    prepare = definition["prepare"]
    if prepare is not None:
        capability, value = prepare
        device_id, reachable = _find_device(home, capability, confirmation.room_id)
        steps.append(
            ResponseStep(
                stage=ResponseStage.PREPARE,
                capability=capability,
                intended_value=value,
                device_id=device_id,
                room_id=confirmation.room_id,
                reachable=reachable,
                detail=(
                    "verified and ready; not sent"
                    if reachable
                    else "no reachable device offers this capability"
                ),
            )
        )

    blocked = tuple(
        BlockedAction(capability=capability, intended_value=value, reason=reason)
        for capability, value, reason in definition["blocked"]
    )

    return ResponsePlan(
        response=response,
        confirmed_by=confirmation.confirmed_by,
        category=confirmation.category.value,
        room_id=confirmation.room_id,
        planned_at=moment,
        steps=tuple(steps),
        blocked=blocked,
        metadata={"severity": confirmation.severity.value},
    )
