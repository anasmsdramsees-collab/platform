"""What a confirmed hazard authorizes, and what it does not (spec §20.4, §20.5).

A confirmation names its response — `NOTIFY_AND_ISOLATE_GAS` — and
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
- **Isolate** cuts the supply. The product owner decided on 2026-08-20 that a
  gas detector reaching its alarm threshold is not a maybe: the reading *is*
  the hazard, and a household that has to be woken up and asked first is a
  household breathing gas while it decides. So a confirmed gas hazard closes
  the valve, and the notification tells people it has been closed rather than
  asking whether it should be.

`ISOLATE` is deliberately not called `EXECUTE`, because it cannot do what a
general execute stage could. Two constraints hold it to one direction:

1. the capability must require a `DETERMINISTIC_SAFETY_RULE` — the same gate
   `PREPARE` uses, so no comfort device is reachable from here;
2. the value must be that capability's **fail-safe** value, and only that.
   `valve.state` may be isolated to `closed` and to nothing else. There is no
   argument to `ResponseStep` that opens a valve, so no confirmed hazard, no
   miscarried rule and no future edit to a response definition can reopen a gas
   supply. Reopening is a person's job, after the leak is fixed.

Unlocking egress and starting ventilation stay blocked. They are not
isolations — they energize something or open a door — and neither was part of
the decision that was made.

Closing a valve on a false alarm costs a household its cooking and hot water
until someone reopens it. Not closing on a real one costs more. That asymmetry
is the whole argument, and it only holds while the direction is fixed.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from syltra_contracts.capability_definitions import Confirmation, get_definition
from syltra_digital_twin.core import HomeState

from syltra_risk_engine.governor import Confirmation as HazardConfirmation

NOTIFICATION_CAPABILITY = "notification.send"


#: The one value each isolable capability may be driven to, and no other.
#: A capability absent from this map cannot be isolated at all.
FAIL_SAFE_VALUES: dict[str, Any] = {
    "valve.state": "closed",
}


class ResponseStage(StrEnum):
    """What a confirmed hazard may cause here.

    There is still no `EXECUTE`. `ISOLATE` is narrower on purpose: it can only
    drive a capability to its single fail-safe value, so the stage that exists
    to close a valve has no way to open one.
    """

    NOTIFY = "NOTIFY"
    PREPARE = "PREPARE"
    ISOLATE = "ISOLATE"


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
        # A PREPARE or ISOLATE step targets something that needs a
        # deterministic rule to act. Preparing a light is not a safety response.
        if (
            self.stage in (ResponseStage.PREPARE, ResponseStage.ISOLATE)
            and definition.confirmation is not Confirmation.DETERMINISTIC_SAFETY_RULE
        ):
            msg = (
                f"{self.capability} does not require a deterministic safety rule; "
                f"{self.stage.value.lower()} is not a hazard response for it"
            )
            raise ValueError(msg)
        # The direction constraint. An ISOLATE step exists to cut a supply, and
        # this is the line that keeps it from restoring one: the value is not
        # chosen by the caller, it is checked against the single fail-safe value
        # the capability declares.
        if self.stage is ResponseStage.ISOLATE:
            fail_safe = FAIL_SAFE_VALUES.get(self.capability)
            if fail_safe is None:
                msg = f"{self.capability} has no fail-safe value and cannot be isolated"
                raise ValueError(msg)
            if self.intended_value != fail_safe:
                msg = (
                    f"an ISOLATE step may only drive {self.capability} to "
                    f"{fail_safe!r}, not {self.intended_value!r}"
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
    def isolating(self) -> tuple[ResponseStep, ...]:
        """Steps that cut a supply, and are meant to be carried out.

        Unlike `prepared`, these are not a plan for a person to approve. They
        are what the platform does on its own the moment a certified detector
        confirms — which is why every one of them is direction-locked by
        `ResponseStep.__post_init__`.
        """
        return tuple(s for s in self.steps if s.stage is ResponseStage.ISOLATE)

    @property
    def unreachable(self) -> tuple[ResponseStep, ...]:
        """Prepared steps whose device the twin cannot vouch for.

        Worth surfacing rather than hiding: a prepared isolation that names no
        reachable valve is a plan that will fail at the moment it matters, and
        the household should learn that now rather than then.
        """
        return tuple(s for s in self.prepared + self.isolating if not s.reachable)


# ── what each authorized response consists of ──

# `prepare` names the capability and the value an isolation would set.
# `blocked` names an action the response calls for that this system will not
# perform without approval, and why.
# Gas isolates. The owner's decision of 2026-08-20: a certified detector at its
# alarm threshold is a hazard, not a question, and the valve closes.
_GAS = {
    "isolate": ("valve.state", "closed"),
    "prepare": None,
    "blocked": (),
}
# Water still prepares. A leak damages property; gas kills people, and the two
# do not deserve the same answer by default. Whether water should also isolate
# automatically is a separate decision nobody has made.
_WATER = {
    "isolate": None,
    "prepare": ("valve.state", "closed"),
    "blocked": (),
}
_EGRESS = {
    "isolate": None,
    "prepare": None,
    # Unlocking is not preparable: there is no half of it that changes nothing.
    "blocked": (("lock.state", "unlocked", "unlocking egress operates a door"),),
}
_VENTILATE = {
    "isolate": None,
    "prepare": None,
    "blocked": (("switch.power", True, "ventilation operates a device"),),
}

RESPONSE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "NOTIFY_AND_ISOLATE_GAS": _GAS,
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

    Never dispatches. Planning and acting stay separate acts: this function
    resolves what should happen, and `isolation.py` is the only thing that
    turns an ISOLATE step into a command — through policy, the orchestrator and
    a verified read-back, none of which live here.
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

    isolate = definition.get("isolate")
    if isolate is not None:
        capability, value = isolate
        device_id, reachable = _find_device(home, capability, confirmation.room_id)
        steps.append(
            ResponseStep(
                stage=ResponseStage.ISOLATE,
                capability=capability,
                intended_value=value,
                device_id=device_id,
                room_id=confirmation.room_id,
                reachable=reachable,
                detail=(
                    "closing now; the household is told, not asked"
                    if reachable
                    else "no reachable device offers this capability"
                ),
            )
        )

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
