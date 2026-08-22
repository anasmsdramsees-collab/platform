"""Proposing a rule instead of proposing an action, every day, forever.

The adaptive engine has always been able to say "turn the living room light on
now, you usually do at this hour". It said it again the next evening, and the
one after. A household that accepted it two hundred times had taught the
platform nothing it could keep.

This turns the same evidence into an **automation** the household can accept
once. `RoutineBaselineModel` already ranks half-hour slots by how firmly a
routine sits in them; a strong slot is a scheduled trigger with the times
already in it.

## The line this must not cross

A proposal is not an automation. Nothing here creates, enables or runs
anything — `propose` returns descriptions, and a person turns one into an
automation through the same endpoint they would have used to write it
themselves. That is deliberate and it is the whole safety argument:

**an action the model got wrong happens once; a rule the model got wrong
happens every day until somebody notices.**

So the bar for proposing is higher than the bar for recommending. A routine has
to be strong *and* consistent across the days it covers before it is worth
offering as a standing instruction, and the proposal carries the evidence in
the form a person can check — which days, how many, how firmly — rather than a
confidence score they have no way to argue with.

## Grouping

Five weekday evenings at 19:00 are one proposal with five weekdays, not five
proposals. A household offered five near-identical rules will accept them all
and then have five things to unpick when the routine changes.

## Identity

The same routine must propose the same automation twice, so a household that
declined last week is not asked again by a proposal wearing a new id.
`proposal_id` is derived from the home, capability and slot rather than
generated.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from syltra_contracts import (
    Automation,
    AutomationAction,
    AutomationTrigger,
    TriggerKind,
)

logger = logging.getLogger(__name__)

#: How firmly a slot must sit before it is worth offering as a standing rule.
#: Higher than the threshold for recommending one action, because the cost of
#: being wrong repeats.
MIN_PROPOSAL_STRENGTH = 0.75

#: A routine on fewer days than this is a habit, not a schedule. Two evenings
#: out of seven is not something to write a rule about.
MIN_DAYS = 3

BUCKETS_PER_DAY = 48
MINUTES_PER_BUCKET = 30


@dataclass(frozen=True)
class AutomationProposal:
    """An automation the platform would write, if the household agreed."""

    proposal_id: UUID
    home_id: str
    capability: str
    device_id: str
    at_hour: int
    at_minute: int
    weekdays: tuple[int, ...]
    strength: float
    proposed_at: datetime

    def as_automation(self, owner: str, name: str) -> Automation:
        """The typed graph this becomes once somebody accepts it.

        Built through the same contracts a person's own automation goes
        through, so a proposal cannot express anything a household could not
        have written by hand — including nothing outside NON_CRITICAL and
        COMFORT, which `AutomationAction` refuses at construction.
        """
        return Automation(
            home_id=self.home_id,
            name=name,
            owner=owner,
            trigger=AutomationTrigger(
                kind=TriggerKind.AT_TIME,
                at_hour=self.at_hour,
                at_minute=self.at_minute,
                weekdays=self.weekdays,
            ),
            actions=(
                AutomationAction(
                    capability=self.capability, value=True, device_id=self.device_id
                ),
            ),
        )

    def as_view(self) -> dict[str, Any]:
        return {
            "proposal_id": str(self.proposal_id),
            "capability": self.capability,
            "device_id": self.device_id,
            "at_hour": self.at_hour,
            "at_minute": self.at_minute,
            "weekdays": list(self.weekdays),
            "strength": round(self.strength, 3),
            # The evidence, in the shape a person can argue with. A confidence
            # score alone is a number nobody can check.
            "days_observed": len(self.weekdays),
            "reason_code": "REPEATED_USER_PATTERN",
            "proposed_at": self.proposed_at.isoformat(),
        }


def propose(
    home_id: str,
    device_id: str,
    capability: str,
    strongest: list[tuple[int, float]],
    now: datetime | None = None,
) -> list[AutomationProposal]:
    """Turn a model's strongest slots into automations worth offering.

    `strongest` is `RoutineBaselineModel.strongest_buckets()` — half-hour slots
    across a week, each with a strength between 0 and 1.
    """
    moment = now or datetime.now(tz=UTC)

    # Slots at the same time of day, gathered across the week: five weekday
    # evenings are one rule, not five.
    by_time: dict[tuple[int, int], list[tuple[int, float]]] = defaultdict(list)
    for bucket, strength in strongest:
        if strength < MIN_PROPOSAL_STRENGTH:
            continue
        weekday, slot = divmod(bucket % (BUCKETS_PER_DAY * 7), BUCKETS_PER_DAY)
        minutes = slot * MINUTES_PER_BUCKET
        by_time[(minutes // 60, minutes % 60)].append((weekday, strength))

    proposals: list[AutomationProposal] = []
    for (hour, minute), days in sorted(by_time.items()):
        if len(days) < MIN_DAYS:
            continue
        weekdays = tuple(sorted(weekday for weekday, _ in days))
        proposals.append(
            AutomationProposal(
                proposal_id=_identity(home_id, device_id, capability, hour, minute),
                home_id=home_id,
                capability=capability,
                device_id=device_id,
                at_hour=hour,
                at_minute=minute,
                weekdays=weekdays,
                strength=min(strength for _, strength in days),
                proposed_at=moment,
            )
        )
    return proposals


def _identity(home_id: str, device_id: str, capability: str, hour: int, minute: int) -> UUID:
    """Stable, so a declined proposal cannot return wearing a new id."""
    return uuid5(NAMESPACE_URL, f"{home_id}/{device_id}/{capability}/{hour:02d}:{minute:02d}")
