"""Who the household is (spec §21, UI-5).

The role table said what each role may do. Nothing said who holds one. Tokens
were minted by a development server and the console's *Users and Roles* screen
was marked unavailable, which is honest and not a product.

## What this enforces, and why each rule exists

**Every change carries a reason.** Not a nicety: a permission change is the one
audit entry somebody reads months later while asking why a guest could open the
garage, and "role changed" without a reason answers nothing. UI-5 asks for it
and `MembershipChange` refuses to be built without it.

**Guest and installer access expires.** An installer commissions a hub over an
afternoon and keeps a key forever unless something takes it back. Expiry is a
property of the membership rather than a task somebody remembers.

**Only an Owner may appoint a Safety Operator.** That role is who a confirmed
gas hazard escalates to, and a household where any adult can quietly appoint one
has not appointed anybody.

**An Owner cannot remove the last Owner.** A household locked out of its own hub
has no recovery path that does not involve a factory reset, which loses the
history that made the hub worth having.

**Nobody grants themselves more than they hold.** Enforced by comparing
permission sets rather than by ranking roles, because a rank order is a thing
people extend without noticing what it now implies.
"""

import logging
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from syltra_security.authorization import ROLE_PERMISSIONS, Permission, Role

logger = logging.getLogger(__name__)

#: Roles that must not outlive the visit that created them, and how long they
#: last when the caller does not say.
DEFAULT_EXPIRY: dict[Role, timedelta] = {
    Role.GUEST: timedelta(hours=24),
    Role.INSTALLER: timedelta(hours=8),
    # Shortest of the three. A support session is one problem, not a
    # relationship: the technician looks, fixes, and the door closes behind
    # them without anybody having to remember to close it.
    Role.SUPPORT: timedelta(hours=4),
}

#: Roles only an Owner may hand out.
OWNER_APPOINTED: frozenset[Role] = frozenset(
    {Role.OWNER, Role.SAFETY_OPERATOR, Role.PANEL}
)
"""A panel is on this list because installing one is a physical decision.

Anybody who can register a panel can put a permanent, always-on control surface
on a wall — and the person who decides where that goes is the person who owns
the house.
"""

#: Roles that are a surface rather than a person. Their actions are attributed
#: to the thing, because inventing a name for whoever pressed a shared panel
#: would be a lie, and an audit trail that lies is worse than one with a gap.
NOT_A_PERSON: frozenset[Role] = frozenset({Role.PANEL, Role.SERVICE})


class MembershipRefused(PermissionError):
    """A change the directory will not make, with a reason code."""

    def __init__(self, reason_code: str, detail: str) -> None:
        super().__init__(f"{reason_code}: {detail}")
        self.reason_code = reason_code
        self.detail = detail


@dataclass(frozen=True)
class Membership:
    """One person's standing in one household."""

    membership_id: UUID
    home_id: str
    subject: str
    role: Role
    display_name: str
    granted_by: str
    granted_at: datetime
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    revoked_by: str | None = None

    def is_active_at(self, now: datetime) -> bool:
        if self.revoked_at is not None and now >= self.revoked_at:
            return False
        return self.expires_at is None or now < self.expires_at

    @property
    def permissions(self) -> frozenset[Permission]:
        return ROLE_PERMISSIONS[self.role]

    def as_view(self, now: datetime) -> dict[str, Any]:
        return {
            "membership_id": str(self.membership_id),
            "subject": self.subject,
            "display_name": self.display_name,
            "role": self.role.value,
            "active": self.is_active_at(now),
            "granted_by": self.granted_by,
            "granted_at": self.granted_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "permissions": sorted(p.value for p in self.permissions),
        }


@dataclass(frozen=True)
class MembershipChange:
    """One entry in the record of who changed whose access, and why."""

    at: datetime
    home_id: str
    action: str
    actor: str
    subject: str
    reason: str
    detail: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # UI-5: permission changes require a confirmation and an audit reason.
        # Refused at construction, so no path can record a change without one.
        if not self.reason.strip():
            msg = "a membership change must carry a reason"
            raise ValueError(msg)


class UserDirectory:
    """The household's members, and the record of every change to them."""

    def __init__(self) -> None:
        self._memberships: dict[str, dict[UUID, Membership]] = {}
        self.audit: list[MembershipChange] = []

    # ── reading ──

    def members(self, home_id: str, now: datetime | None = None) -> list[Membership]:
        """Everyone on record, active or not, newest grant first.

        Revoked and expired memberships stay visible rather than disappearing:
        "who used to have a key" is the question somebody asks after something
        goes missing.
        """
        moment = now or datetime.now(tz=UTC)
        found = list(self._memberships.get(home_id, {}).values())
        return sorted(found, key=lambda m: (not m.is_active_at(moment), -m.granted_at.timestamp()))

    def active_roles(self, home_id: str, subject: str, now: datetime | None = None) -> set[Role]:
        moment = now or datetime.now(tz=UTC)
        return {
            m.role
            for m in self._memberships.get(home_id, {}).values()
            if m.subject == subject and m.is_active_at(moment)
        }

    def owners(self, home_id: str, now: datetime | None = None) -> list[Membership]:
        moment = now or datetime.now(tz=UTC)
        return [
            m
            for m in self._memberships.get(home_id, {}).values()
            if m.role is Role.OWNER and m.is_active_at(moment)
        ]

    # ── changing ──

    def grant(
        self,
        home_id: str,
        subject: str,
        role: Role,
        *,
        actor: str,
        actor_role: Role,
        reason: str,
        display_name: str | None = None,
        expires_at: datetime | None = None,
        now: datetime | None = None,
    ) -> Membership:
        """Give somebody a role in a household."""
        moment = now or datetime.now(tz=UTC)
        self._check_may_manage(actor_role, role, action="grant")

        if expires_at is None and role in DEFAULT_EXPIRY:
            expires_at = moment + DEFAULT_EXPIRY[role]
        if expires_at is not None and expires_at <= moment:
            msg = "an access grant that has already expired grants nothing"
            raise MembershipRefused("EXPIRY_IN_THE_PAST", msg)

        membership = Membership(
            membership_id=uuid4(),
            home_id=home_id,
            subject=subject,
            role=role,
            display_name=display_name or subject,
            granted_by=actor,
            granted_at=moment,
            expires_at=expires_at,
        )
        self._memberships.setdefault(home_id, {})[membership.membership_id] = membership
        self._record(
            moment,
            home_id,
            "MEMBERSHIP_GRANTED",
            actor,
            subject,
            reason,
            {"role": role.value, "expires_at": expires_at.isoformat() if expires_at else None},
        )
        return membership

    def change_role(
        self,
        home_id: str,
        membership_id: UUID,
        role: Role,
        *,
        actor: str,
        actor_role: Role,
        reason: str,
        now: datetime | None = None,
    ) -> Membership:
        moment = now or datetime.now(tz=UTC)
        existing = self._require(home_id, membership_id)
        self._check_may_manage(actor_role, role, action="assign")
        # Demoting an owner is also a change *from* an owner-appointed role.
        self._check_may_manage(actor_role, existing.role, action="change")
        if existing.role is Role.OWNER and role is not Role.OWNER:
            self._check_not_the_last_owner(home_id, membership_id, moment)

        updated = Membership(
            membership_id=existing.membership_id,
            home_id=existing.home_id,
            subject=existing.subject,
            role=role,
            display_name=existing.display_name,
            granted_by=actor,
            granted_at=moment,
            expires_at=existing.expires_at,
        )
        self._memberships[home_id][membership_id] = updated
        self._record(
            moment,
            home_id,
            "MEMBERSHIP_ROLE_CHANGED",
            actor,
            existing.subject,
            reason,
            {"from": existing.role.value, "to": role.value},
        )
        return updated

    def revoke(
        self,
        home_id: str,
        membership_id: UUID,
        *,
        actor: str,
        actor_role: Role,
        reason: str,
        now: datetime | None = None,
    ) -> Membership:
        moment = now or datetime.now(tz=UTC)
        existing = self._require(home_id, membership_id)
        self._check_may_manage(actor_role, existing.role, action="revoke")
        if existing.role is Role.OWNER:
            self._check_not_the_last_owner(home_id, membership_id, moment)

        revoked = Membership(
            membership_id=existing.membership_id,
            home_id=existing.home_id,
            subject=existing.subject,
            role=existing.role,
            display_name=existing.display_name,
            granted_by=existing.granted_by,
            granted_at=existing.granted_at,
            expires_at=existing.expires_at,
            revoked_at=moment,
            revoked_by=actor,
        )
        self._memberships[home_id][membership_id] = revoked
        self._record(
            moment,
            home_id,
            "MEMBERSHIP_REVOKED",
            actor,
            existing.subject,
            reason,
            {"role": existing.role.value},
        )
        return revoked

    # ── the rules ──

    def _check_may_manage(self, actor_role: Role, target_role: Role, *, action: str) -> None:
        if Permission.MANAGE_USERS not in ROLE_PERMISSIONS[actor_role]:
            msg = f"{actor_role.value} may not {action} memberships"
            raise MembershipRefused("MAY_NOT_MANAGE_USERS", msg)
        if target_role in OWNER_APPOINTED and actor_role is not Role.OWNER:
            msg = f"only an Owner may {action} the {target_role.value} role"
            raise MembershipRefused("OWNER_APPOINTED_ROLE", msg)
        # Nobody hands out more than they hold. Compared as sets rather than by
        # rank: a rank order is a thing people extend without noticing what it
        # now implies.
        granted = ROLE_PERMISSIONS[target_role] - ROLE_PERMISSIONS[actor_role]
        if granted:
            names = ", ".join(sorted(p.value for p in granted))
            msg = f"{actor_role.value} cannot grant permissions it does not hold: {names}"
            raise MembershipRefused("CANNOT_GRANT_BEYOND_OWN_AUTHORITY", msg)

    def _check_not_the_last_owner(self, home_id: str, membership_id: UUID, now: datetime) -> None:
        remaining = [m for m in self.owners(home_id, now) if m.membership_id != membership_id]
        if not remaining:
            msg = (
                "this is the household's only owner; removing it would leave the "
                "hub with no one able to recover it"
            )
            raise MembershipRefused("LAST_OWNER", msg)

    def _require(self, home_id: str, membership_id: UUID) -> Membership:
        found = self._memberships.get(home_id, {}).get(membership_id)
        if found is None:
            msg = f"no membership {membership_id} in {home_id}"
            raise MembershipRefused("NO_SUCH_MEMBERSHIP", msg)
        return found

    def _record(
        self,
        at: datetime,
        home_id: str,
        action: str,
        actor: str,
        subject: str,
        reason: str,
        detail: dict[str, Any],
    ) -> None:
        change = MembershipChange(
            at=at,
            home_id=home_id,
            action=action,
            actor=actor,
            subject=subject,
            reason=reason,
            detail=detail,
        )
        self.audit.append(change)
        logger.info("%s in %s: %s by %s (%s)", action, home_id, subject, actor, reason)

    def changes(self, home_id: str) -> Iterator[MembershipChange]:
        return (change for change in self.audit if change.home_id == home_id)
