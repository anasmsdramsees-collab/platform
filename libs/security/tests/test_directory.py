"""Who the household is, and who may change it (spec §21, UI-5).

The interesting tests here are the refusals. A directory that grants access
correctly and refuses nothing is a directory that hands out keys.
"""

from datetime import UTC, datetime, timedelta

import pytest
from syltra_security import (
    ROLE_PERMISSIONS,
    Membership,
    MembershipChange,
    MembershipRefused,
    Permission,
    Role,
    UserDirectory,
)

NOW = datetime(2026, 8, 20, 18, 0, tzinfo=UTC)
HOME = "home_directory"


def directory_with_owner() -> tuple[UserDirectory, Membership]:
    directory = UserDirectory()
    owner = directory.grant(
        HOME,
        "amal",
        Role.OWNER,
        actor="bootstrap",
        actor_role=Role.OWNER,
        reason="household set up",
        now=NOW,
    )
    return directory, owner


# ── every change is attributable ──


def test_a_change_without_a_reason_cannot_be_constructed() -> None:
    """UI-5 asks for a reason, and this refuses to be built without one.

    A permission change is the audit entry somebody reads months later while
    asking why a guest could open the garage. "Role changed" answers nothing.
    """
    with pytest.raises(ValueError, match="must carry a reason"):
        MembershipChange(
            at=NOW, home_id=HOME, action="MEMBERSHIP_GRANTED", actor="a", subject="b", reason="   "
        )


def test_every_grant_and_revocation_is_recorded_with_its_reason() -> None:
    directory, owner = directory_with_owner()
    guest = directory.grant(
        HOME,
        "visitor",
        Role.GUEST,
        actor="amal",
        actor_role=Role.OWNER,
        reason="staying the weekend",
        now=NOW,
    )
    directory.revoke(
        HOME,
        guest.membership_id,
        actor="amal",
        actor_role=Role.OWNER,
        reason="visit ended",
        now=NOW + timedelta(days=2),
    )

    reasons = [change.reason for change in directory.changes(HOME)]
    assert "staying the weekend" in reasons
    assert "visit ended" in reasons
    assert owner.granted_by == "bootstrap"


# ── access that ends by itself ──


def test_guest_access_expires_without_anybody_remembering() -> None:
    directory, _ = directory_with_owner()
    guest = directory.grant(
        HOME,
        "visitor",
        Role.GUEST,
        actor="amal",
        actor_role=Role.OWNER,
        reason="one night",
        now=NOW,
    )
    assert guest.is_active_at(NOW + timedelta(hours=23))
    assert not guest.is_active_at(NOW + timedelta(hours=25))


def test_installer_access_expires_sooner_than_a_guest() -> None:
    """An installer commissions a hub over an afternoon, not a weekend."""
    directory, _ = directory_with_owner()
    installer = directory.grant(
        HOME,
        "fitter",
        Role.INSTALLER,
        actor="amal",
        actor_role=Role.OWNER,
        reason="commissioning the hub",
        now=NOW,
    )
    assert not installer.is_active_at(NOW + timedelta(hours=9))


def test_an_owner_does_not_expire() -> None:
    _, owner = directory_with_owner()
    assert owner.expires_at is None
    assert owner.is_active_at(NOW + timedelta(days=3650))


def test_a_grant_that_has_already_expired_is_refused() -> None:
    directory, _ = directory_with_owner()
    with pytest.raises(MembershipRefused, match="EXPIRY_IN_THE_PAST"):
        directory.grant(
            HOME,
            "visitor",
            Role.GUEST,
            actor="amal",
            actor_role=Role.OWNER,
            reason="backdated",
            expires_at=NOW - timedelta(minutes=1),
            now=NOW,
        )


# ── the refusals ──


def test_a_resident_cannot_manage_anybody() -> None:
    directory, _ = directory_with_owner()
    with pytest.raises(MembershipRefused, match="MAY_NOT_MANAGE_USERS"):
        directory.grant(
            HOME,
            "stranger",
            Role.GUEST,
            actor="teenager",
            actor_role=Role.ADULT,
            reason="a friend is over",
            now=NOW,
        )


def test_nobody_grants_a_permission_they_do_not_hold() -> None:
    """Compared as permission sets, not by rank.

    A rank order is a thing people extend without noticing what it now implies.
    """
    directory, _ = directory_with_owner()
    # Contrived, but this is the shape of the mistake: a role that can manage
    # users without holding everything it might hand out.
    with pytest.raises(MembershipRefused):
        directory.grant(
            HOME,
            "someone",
            Role.OWNER,
            actor="fitter",
            actor_role=Role.INSTALLER,
            reason="handing over",
            now=NOW,
        )


def test_an_owner_may_appoint_a_safety_operator() -> None:
    """The role a confirmed gas hazard escalates to."""
    directory, _ = directory_with_owner()
    appointed = directory.grant(
        HOME,
        "neighbour",
        Role.SAFETY_OPERATOR,
        actor="amal",
        actor_role=Role.OWNER,
        reason="agreed to be called if the gas alarm sounds",
        now=NOW,
    )
    assert appointed.role is Role.SAFETY_OPERATOR


def test_nobody_but_an_owner_can_reach_the_appointment_at_all() -> None:
    """Two gates, and today the first one is doing the work.

    An ADULT is stopped by MAY_NOT_MANAGE_USERS before OWNER_APPOINTED_ROLE is
    ever consulted, because OWNER is currently the only role holding
    MANAGE_USERS. The second gate exists for the household-admin role the
    directive asks for: the moment somebody who can manage users is not an
    owner, appointing a Safety Operator must still be out of reach.
    """
    directory, _ = directory_with_owner()
    with pytest.raises(MembershipRefused, match="MAY_NOT_MANAGE_USERS"):
        directory.grant(
            HOME,
            "someone_else",
            Role.SAFETY_OPERATOR,
            actor="teenager",
            actor_role=Role.ADULT,
            reason="seems responsible",
            now=NOW,
        )

    # The claim the paragraph above rests on, asserted rather than believed.
    managers = {
        role
        for role, permissions in ROLE_PERMISSIONS.items()
        if Permission.MANAGE_USERS in permissions
    }
    assert managers == {Role.OWNER}, (
        "a non-owner can now manage users; OWNER_APPOINTED_ROLE is load-bearing "
        "and needs its own test"
    )


def test_the_last_owner_cannot_be_revoked() -> None:
    """A hub with no owner has no recovery that is not a factory reset."""
    directory, owner = directory_with_owner()
    with pytest.raises(MembershipRefused, match="LAST_OWNER"):
        directory.revoke(
            HOME,
            owner.membership_id,
            actor="amal",
            actor_role=Role.OWNER,
            reason="leaving",
            now=NOW,
        )


def test_the_last_owner_cannot_be_demoted_either() -> None:
    directory, owner = directory_with_owner()
    with pytest.raises(MembershipRefused, match="LAST_OWNER"):
        directory.change_role(
            HOME,
            owner.membership_id,
            Role.ADULT,
            actor="amal",
            actor_role=Role.OWNER,
            reason="stepping back",
            now=NOW,
        )


def test_an_owner_may_leave_once_another_owner_exists() -> None:
    directory, owner = directory_with_owner()
    directory.grant(
        HOME,
        "partner",
        Role.OWNER,
        actor="amal",
        actor_role=Role.OWNER,
        reason="joint household",
        now=NOW,
    )
    revoked = directory.revoke(
        HOME,
        owner.membership_id,
        actor="partner",
        actor_role=Role.OWNER,
        reason="moved out",
        now=NOW + timedelta(days=1),
    )
    assert not revoked.is_active_at(NOW + timedelta(days=2))
    assert len(directory.owners(HOME, NOW + timedelta(days=2))) == 1


# ── what stays visible ──


def test_a_revoked_membership_is_still_listed() -> None:
    """ "Who used to have a key" is the question asked after something goes
    missing, and a directory that forgets cannot answer it."""
    directory, _ = directory_with_owner()
    guest = directory.grant(
        HOME,
        "visitor",
        Role.GUEST,
        actor="amal",
        actor_role=Role.OWNER,
        reason="weekend",
        now=NOW,
    )
    directory.revoke(
        HOME,
        guest.membership_id,
        actor="amal",
        actor_role=Role.OWNER,
        reason="left",
        now=NOW + timedelta(days=1),
    )
    listed = directory.members(HOME, NOW + timedelta(days=2))
    assert any(m.membership_id == guest.membership_id for m in listed)
    assert [m.is_active_at(NOW + timedelta(days=2)) for m in listed] == [True, False]


# ── the role that is named after safety and holds none of it ──


def test_a_safety_operator_commands_nothing() -> None:
    """It can say an incident is over. It cannot touch a valve.

    That distinction is the entire reason this role can exist without breaking
    invariants 6, 13 and 18.
    """
    directory, _ = directory_with_owner()
    appointed = directory.grant(
        HOME,
        "neighbour",
        Role.SAFETY_OPERATOR,
        actor="amal",
        actor_role=Role.OWNER,
        reason="on call",
        now=NOW,
    )
    assert Permission.ACKNOWLEDGE_SAFETY in appointed.permissions
    assert Permission.ACT_SAFETY not in appointed.permissions
    assert Permission.ACT_COMFORT not in appointed.permissions
    assert Permission.ACT_SECURITY not in appointed.permissions
