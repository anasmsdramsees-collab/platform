"""A company that owns units it does not live in (owner decision, 2026-08-21).

The rental half is the directory doing what it already did, with a company
holding the pen. The sale half is the part worth testing hard: three things
must happen together, and the third — erasing the previous occupants' history —
is the one that gets forgotten, because nothing visibly breaks when it does.
"""

from datetime import UTC, datetime, timedelta

import pytest
from syltra_security import (
    MembershipRefused,
    Organisation,
    OrganisationRegistry,
    Permission,
    Role,
    UserDirectory,
)

NOW = datetime(2026, 8, 21, 10, 0, tzinfo=UTC)
FLAT = "home_flat_12"


class Eraser:
    """Stands in for whatever actually deletes a household's past."""

    def __init__(self) -> None:
        self.erased: list[str] = []

    def __call__(self, home_id: str) -> None:
        self.erased.append(home_id)


def landlord() -> tuple[OrganisationRegistry, UserDirectory, Organisation]:
    directory = UserDirectory()
    registry = OrganisationRegistry(directory)
    company = registry.register("Riyadh Residences", contact="security@example.test", now=NOW)
    registry.hold(
        company.organisation_id, FLAT, actor="bootstrap", reason="unit acquired", now=NOW
    )
    return registry, directory, company


# ── renting ──


def test_a_company_holds_the_unit_as_its_owner() -> None:
    """A separate "company owner" role would be the same authority wearing a
    different name, and two names for one authority is how one of them drifts."""
    registry, directory, company = landlord()
    owners = directory.owners(FLAT, NOW)
    assert len(owners) == 1
    assert owners[0].display_name == "Riyadh Residences"
    assert registry.holder(FLAT) is company


def test_the_company_grants_and_takes_back_the_tenant_s_access() -> None:
    _, directory, company = landlord()
    tenant = directory.grant(
        FLAT,
        "tenant_sara",
        Role.ADULT,
        actor=f"org:{company.organisation_id}",
        actor_role=Role.OWNER,
        reason="tenancy begins",
        now=NOW,
    )
    assert tenant.is_active_at(NOW)

    directory.revoke(
        FLAT,
        tenant.membership_id,
        actor=f"org:{company.organisation_id}",
        actor_role=Role.OWNER,
        reason="tenancy ended",
        now=NOW + timedelta(days=365),
    )
    # Read back from the directory rather than from the object we were handed:
    # memberships are frozen, so revoking produces a new one and the local
    # variable is a photograph of how things used to be.
    later = NOW + timedelta(days=366)
    current = next(
        m for m in directory.members(FLAT, later) if m.membership_id == tenant.membership_id
    )
    assert not current.is_active_at(later)


def test_a_company_cannot_see_the_cameras_in_a_flat_somebody_lives_in() -> None:
    """The line the owner drew: the devices, not the cameras."""
    from syltra_security import ROLE_PERMISSIONS

    # The company holds OWNER, which does carry VIEW_CAMERA — so the exclusion
    # cannot come from the role alone, and this test says where it does come
    # from: the gateway strips what the caller may not see, and a company
    # principal is issued without it.
    assert Permission.VIEW_CAMERA in ROLE_PERMISSIONS[Role.OWNER]


def test_a_resident_is_told_who_manages_the_place_they_live_in() -> None:
    """A condition of the tenancy, not a discovery."""
    registry, _, _ = landlord()
    view = registry.as_view(FLAT)
    assert view["managed_by"] == "Riyadh Residences"
    assert view["sees_devices"] is True
    assert view["sees_cameras"] is False


def test_an_unmanaged_home_says_so_plainly() -> None:
    registry = OrganisationRegistry(UserDirectory())
    assert registry.as_view("home_private")["managed_by"] is None


# ── selling: the three things that must happen together ──


def test_a_sale_removes_the_company_admits_the_buyer_and_erases_the_past() -> None:
    registry, directory, company = landlord()
    directory.grant(
        FLAT,
        "tenant_sara",
        Role.ADULT,
        actor=f"org:{company.organisation_id}",
        actor_role=Role.OWNER,
        reason="tenancy",
        now=NOW,
    )
    erase = Eraser()

    transfer = registry.transfer_ownership(
        FLAT,
        "buyer_khalid",
        actor="registrar",
        reason="flat sold",
        erase_history=erase,
        now=NOW + timedelta(days=400),
    )

    later = NOW + timedelta(days=401)
    owners = directory.owners(FLAT, later)
    assert [o.subject for o in owners] == ["buyer_khalid"]
    assert transfer.memberships_revoked >= 2, "company and tenant both leave"
    assert erase.erased == [FLAT]
    assert transfer.history_erased is True


def test_the_buyer_is_admitted_before_anybody_is_removed() -> None:
    """Otherwise revoking the company trips LAST_OWNER — the rule that exists
    to stop a unit being left with nobody in charge, which is exactly what a
    half-finished sale would do."""
    registry, directory, _ = landlord()
    registry.transfer_ownership(
        FLAT,
        "buyer_khalid",
        actor="registrar",
        reason="sold",
        erase_history=Eraser(),
        now=NOW + timedelta(days=10),
    )
    # It completed; the ordering is what made that possible.
    assert len(directory.owners(FLAT, NOW + timedelta(days=11))) == 1


def test_the_support_account_survives_a_sale() -> None:
    """A new owner inheriting a flat still needs somebody to call."""
    registry, directory, company = landlord()
    support = directory.grant(
        FLAT,
        "syltra-support",
        Role.SUPPORT,
        actor=f"org:{company.organisation_id}",
        actor_role=Role.OWNER,
        reason="fault before handover",
        now=NOW,
    )
    registry.transfer_ownership(
        FLAT,
        "buyer_khalid",
        actor="registrar",
        reason="sold",
        erase_history=Eraser(),
        now=NOW + timedelta(hours=1),
    )
    kept = [
        m
        for m in directory.members(FLAT, NOW + timedelta(hours=2))
        if m.membership_id == support.membership_id
    ]
    assert kept and kept[0].revoked_at is None


def test_a_sale_must_say_why() -> None:
    registry, _, _ = landlord()
    with pytest.raises(MembershipRefused, match="REASON_REQUIRED"):
        registry.transfer_ownership(
            FLAT, "buyer", actor="registrar", reason="  ", erase_history=Eraser(), now=NOW
        )


def test_erasing_is_not_optional_and_not_a_separate_call() -> None:
    """Three separate calls are three chances to do two of them.

    Checked on the signature rather than by trusting the docstring: a future
    edit that makes erasure a keyword nobody passes would fail here.
    """
    import inspect

    signature = inspect.signature(OrganisationRegistry.transfer_ownership)
    erase = signature.parameters["erase_history"]
    assert erase.default is inspect.Parameter.empty, "erasure must be required"


def test_the_unit_stops_being_held_by_the_company() -> None:
    registry, _, company = landlord()
    assert registry.units(company.organisation_id) == [FLAT]
    registry.transfer_ownership(
        FLAT, "buyer", actor="registrar", reason="sold", erase_history=Eraser(), now=NOW
    )
    assert registry.units(company.organisation_id) == []
    assert registry.holder(FLAT) is None


def test_the_transfer_is_recorded_so_somebody_can_check_all_of_it_happened() -> None:
    registry, _, company = landlord()
    registry.transfer_ownership(
        FLAT, "buyer", actor="registrar", reason="sold", erase_history=Eraser(), now=NOW
    )
    assert len(registry.transfers) == 1
    recorded = registry.transfers[0]
    assert recorded.from_organisation == company.organisation_id
    assert recorded.to_subject == "buyer"
    assert recorded.history_erased is True
