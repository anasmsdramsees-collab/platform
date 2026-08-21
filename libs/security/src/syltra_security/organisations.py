"""A company that owns units it does not live in (owner decision, 2026-08-21).

Most of this platform assumes a household: people who live somewhere, and who
between them are the owner. A property company is the other case — it holds the
apartments, rents them out, grants the tenant access, takes it back when the
tenancy ends, and one day sells the flat to somebody who then owns it outright.

## The two things that make this different from a bigger household

**The company is the owner of record and does not live there.** So the tenant is
not an owner: they are a resident whose membership the company grants and
revokes. That is `UserDirectory` unchanged — no new mechanism, just a different
hand holding it.

**Selling is not a role change.** It is three things that must happen together
or not at all, and the third is the one that gets forgotten:

1. the company loses access — a former owner is not a quiet observer;
2. the buyer becomes the owner;
3. **the previous occupants' history is destroyed.**

There is no reason a buyer should learn when the last tenant slept, and this
platform knows that because knowing it is its job. `transfer_ownership` is a
single call for exactly this reason: three separate calls are three chances to
do two of them.

## What a company may see, and what it may not

Whatever `ROLE_PERMISSIONS` says, minus the cameras — enforced by
`VIEW_CAMERA` sitting in no company role rather than by an exception carved out
by capability name. The owner drew that line on 2026-08-21.

The tenant is told. A company that can see the devices in the flat somebody
lives in is a condition of the tenancy, not a discovery, and the console says so
on the Users and Roles screen.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from syltra_security.authorization import Role
from syltra_security.directory import Membership, MembershipRefused, UserDirectory

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Organisation:
    """A company holding units — a landlord, a developer, a facilities operator."""

    organisation_id: UUID
    name: str
    #: The department a company answers with. Recorded because "the company can
    #: see it" is not a person, and an audit trail naming a company names
    #: nobody.
    contact: str
    created_at: datetime


@dataclass(frozen=True)
class UnitTransfer:
    """What a sale did, kept so somebody can check all of it happened."""

    home_id: str
    from_organisation: UUID | None
    to_subject: str
    at: datetime
    memberships_revoked: int
    history_erased: bool
    reason: str


class OrganisationRegistry:
    """Companies, the units they hold, and what happens when one is sold."""

    def __init__(self, directory: UserDirectory) -> None:
        self._directory = directory
        self._organisations: dict[UUID, Organisation] = {}
        self._units: dict[str, UUID] = {}
        self.transfers: list[UnitTransfer] = []

    # ── companies and their units ──

    def register(self, name: str, contact: str, now: datetime | None = None) -> Organisation:
        organisation = Organisation(
            organisation_id=uuid4(),
            name=name,
            contact=contact,
            created_at=now or datetime.now(tz=UTC),
        )
        self._organisations[organisation.organisation_id] = organisation
        return organisation

    def hold(
        self,
        organisation_id: UUID,
        home_id: str,
        *,
        actor: str,
        reason: str,
        now: datetime | None = None,
    ) -> Membership:
        """Record that a company holds a unit, and give it the owner's standing.

        The company becomes `OWNER` of the unit because that is what it is: the
        party who decides who may enter. A separate "company owner" role would
        be the same authority wearing a different name, and two names for one
        authority is how one of them drifts.
        """
        organisation = self._require(organisation_id)
        self._units[home_id] = organisation_id
        return self._directory.grant(
            home_id,
            subject=f"org:{organisation_id}",
            role=Role.OWNER,
            actor=actor,
            actor_role=Role.OWNER,
            reason=reason,
            display_name=organisation.name,
            now=now,
        )

    def holder(self, home_id: str) -> Organisation | None:
        organisation_id = self._units.get(home_id)
        return None if organisation_id is None else self._organisations.get(organisation_id)

    def units(self, organisation_id: UUID) -> list[str]:
        return sorted(home for home, held in self._units.items() if held == organisation_id)

    # ── selling ──

    def transfer_ownership(
        self,
        home_id: str,
        to_subject: str,
        *,
        actor: str,
        reason: str,
        erase_history: Callable[[str], None],
        display_name: str | None = None,
        keep: frozenset[Role] = frozenset({Role.SUPPORT}),
        now: datetime | None = None,
    ) -> UnitTransfer:
        """Sell a unit: the company leaves, the buyer arrives, the past is erased.

        One call, because three calls are three chances to do two of them. The
        order matters and is not an implementation detail:

        the buyer is made owner **first**, so the last-owner rule never sees a
        unit with nobody in charge and refuse the very revocation the sale
        depends on. Then everyone else is revoked. Then the history goes.

        `erase_history` is injected rather than imported. This module knows who
        may hold a unit; it has no business knowing how a twin or an event store
        deletes a household's past, and wiring it in would make a permissions
        library a data-deletion library.

        `keep` defaults to the support account, which the owner asked to survive
        a sale — a new owner inheriting a flat still needs somebody to call.
        """
        moment = now or datetime.now(tz=UTC)
        if not reason.strip():
            msg = "a change of ownership must say why"
            raise MembershipRefused("REASON_REQUIRED", msg)

        held_by = self._units.get(home_id)

        # The buyer first. Otherwise revoking the company trips LAST_OWNER,
        # which exists to stop a unit being left with nobody able to recover it
        # — exactly what a half-finished sale would do.
        self._directory.grant(
            home_id,
            subject=to_subject,
            role=Role.OWNER,
            actor=actor,
            actor_role=Role.OWNER,
            reason=reason,
            display_name=display_name or to_subject,
            now=moment,
        )

        revoked = 0
        for membership in list(self._directory.members(home_id, moment)):
            if membership.subject == to_subject or not membership.is_active_at(moment):
                continue
            if membership.role in keep:
                continue
            self._directory.revoke(
                home_id,
                membership.membership_id,
                actor=actor,
                actor_role=Role.OWNER,
                reason=reason,
                now=moment,
            )
            revoked += 1

        # Last, and not optional. A buyer has no business learning when the
        # previous tenant slept, and the platform knows that because knowing it
        # is its job.
        erase_history(home_id)
        self._units.pop(home_id, None)

        transfer = UnitTransfer(
            home_id=home_id,
            from_organisation=held_by,
            to_subject=to_subject,
            at=moment,
            memberships_revoked=revoked,
            history_erased=True,
            reason=reason,
        )
        self.transfers.append(transfer)
        logger.info(
            "unit %s transferred to %s: %d memberships revoked, history erased (%s)",
            home_id,
            to_subject,
            revoked,
            reason,
        )
        return transfer

    def _require(self, organisation_id: UUID) -> Organisation:
        found = self._organisations.get(organisation_id)
        if found is None:
            msg = f"no organisation {organisation_id}"
            raise MembershipRefused("NO_SUCH_ORGANISATION", msg)
        return found

    def as_view(self, home_id: str) -> dict[str, Any]:
        """What a resident is told about who manages the place they live in."""
        organisation = self.holder(home_id)
        if organisation is None:
            return {"managed_by": None}
        return {
            "managed_by": organisation.name,
            "contact": organisation.contact,
            # Said plainly, because it is a condition of the tenancy rather
            # than something to be discovered.
            "sees_devices": True,
            "sees_cameras": False,
        }
