"""Authorization and token tests (spec §25.1, §25.3).

Phase 7 acceptance: authorization isolates homes and roles.
"""

from datetime import UTC, datetime, timedelta

import pytest
from syltra_contracts import SafetyClass
from syltra_contracts.capability_definitions import CAPABILITY_DEFINITIONS
from syltra_security import (
    ROLE_PERMISSIONS,
    AuthenticationError,
    AuthorizationError,
    Permission,
    Principal,
    Role,
    TokenStore,
    authorize,
    authorize_capability,
    bearer_token,
    hash_token,
    permission_for_capability,
)

NOW = datetime(2026, 8, 19, 12, 0, tzinfo=UTC)


def principal(role: Role = Role.ADULT, homes: set[str] | None = None) -> Principal:
    return Principal(
        subject=f"user_{role.value.lower()}",
        role=role,
        home_ids=frozenset(homes or {"home_001"}),
    )


# ── home isolation ──


@pytest.mark.safety
def test_a_principal_cannot_reach_another_household() -> None:
    with pytest.raises(AuthorizationError) as exc:
        authorize(principal(), "home_other", Permission.READ_HOME)
    assert exc.value.code == "HOME_NOT_FOUND"


@pytest.mark.safety
def test_home_scope_is_checked_before_permission() -> None:
    # Reporting "insufficient permission" for a home the caller cannot see
    # would confirm that the home exists.
    guest = principal(Role.GUEST)
    with pytest.raises(AuthorizationError) as exc:
        authorize(guest, "home_other", Permission.MANAGE_POLICY)
    assert exc.value.code == "HOME_NOT_FOUND"


def test_a_principal_may_belong_to_several_homes() -> None:
    multi = principal(homes={"home_a", "home_b"})
    authorize(multi, "home_a", Permission.READ_HOME)
    authorize(multi, "home_b", Permission.READ_HOME)
    with pytest.raises(AuthorizationError):
        authorize(multi, "home_c", Permission.READ_HOME)


# ── role separation ──


@pytest.mark.safety
def test_no_role_holds_safety_actuator_authority() -> None:
    # Safety invariants 6, 13 and 18: life-safety actuators are commanded by
    # deterministic rules, never by a person holding a permission.
    for role, permissions in ROLE_PERMISSIONS.items():
        assert Permission.ACT_SAFETY not in permissions, f"{role} holds ACT_SAFETY"


@pytest.mark.safety
def test_comfort_authority_does_not_imply_security_authority() -> None:
    # Spec §25.1: separate permissions for comfort, security and safety.
    child = principal(Role.CHILD)
    authorize(child, "home_001", Permission.ACT_COMFORT)
    with pytest.raises(AuthorizationError) as exc:
        authorize(child, "home_001", Permission.ACT_SECURITY)
    assert exc.value.code == "INSUFFICIENT_PERMISSION"


def test_a_guest_may_only_look() -> None:
    guest = principal(Role.GUEST)
    authorize(guest, "home_001", Permission.READ_HOME)
    for denied in (
        Permission.ACT_COMFORT,
        Permission.ACT_SECURITY,
        Permission.APPROVE_RECOMMENDATION,
        Permission.READ_AUDIT,
        Permission.MANAGE_PRIVACY,
    ):
        with pytest.raises(AuthorizationError):
            authorize(guest, "home_001", denied)


def test_only_the_owner_manages_policy_models_and_privacy() -> None:
    for permission in (
        Permission.MANAGE_POLICY,
        Permission.MANAGE_MODELS,
        Permission.MANAGE_PRIVACY,
    ):
        authorize(principal(Role.OWNER), "home_001", permission)
        for role in (Role.ADULT, Role.CHILD, Role.GUEST, Role.INSTALLER):
            with pytest.raises(AuthorizationError):
                authorize(principal(role), "home_001", permission)


def test_an_installer_cannot_read_the_audit_trail_or_operate_locks() -> None:
    # An installer commissions hardware; they are not a household member.
    installer = principal(Role.INSTALLER)
    authorize(installer, "home_001", Permission.READ_HOME)
    for denied in (Permission.READ_AUDIT, Permission.ACT_SECURITY):
        with pytest.raises(AuthorizationError):
            authorize(installer, "home_001", denied)


def test_a_child_cannot_approve_automation() -> None:
    with pytest.raises(AuthorizationError):
        authorize(principal(Role.CHILD), "home_001", Permission.APPROVE_RECOMMENDATION)


# ── capability-derived authority ──


@pytest.mark.safety
def test_every_capability_maps_to_a_permission_matching_its_safety_class() -> None:
    # Derived from the declared safety class, so a new capability cannot be
    # added without inheriting the right authority requirement.
    for capability, definition in CAPABILITY_DEFINITIONS.items():
        permission = permission_for_capability(capability)
        if definition.safety_class in {
            SafetyClass.LIFE_SAFETY_CRITICAL,
            SafetyClass.SAFETY_RELATED,
        }:
            assert permission is Permission.ACT_SAFETY
        elif definition.safety_class is SafetyClass.SECURITY_SENSITIVE:
            assert permission is Permission.ACT_SECURITY
        else:
            assert permission is Permission.ACT_COMFORT


@pytest.mark.safety
def test_nobody_can_command_a_life_safety_capability() -> None:
    # Because ACT_SAFETY belongs to no role, this holds for every role at once.
    for role in Role:
        for capability in ("valve.state", "breaker.state", "siren.state"):
            with pytest.raises(AuthorizationError):
                authorize_capability(principal(role), "home_001", capability)


def test_an_adult_may_command_a_lock_but_a_child_may_not() -> None:
    authorize_capability(principal(Role.ADULT), "home_001", "lock.state")
    with pytest.raises(AuthorizationError):
        authorize_capability(principal(Role.CHILD), "home_001", "lock.state")


def test_a_child_may_command_a_light() -> None:
    authorize_capability(principal(Role.CHILD), "home_001", "light.power")


# ── tokens ──


def test_a_token_is_returned_once_and_stored_only_as_a_hash() -> None:
    store = TokenStore()
    token, record = store.issue("owner", Role.OWNER, {"home_001"}, now=NOW)
    assert token
    assert record.token_hash == hash_token(token)
    assert token not in record.token_hash
    # The plaintext appears nowhere in the record.
    assert token not in repr(record)


def test_a_valid_token_resolves_to_its_principal() -> None:
    store = TokenStore()
    token, _ = store.issue("owner", Role.OWNER, {"home_001"}, now=NOW)
    resolved = store.verify(token, now=NOW)
    assert resolved.subject == "owner"
    assert resolved.role is Role.OWNER
    assert resolved.sees("home_001")


@pytest.mark.parametrize(
    ("token", "code"),
    [("", "MISSING_TOKEN"), ("not-a-real-token", "INVALID_TOKEN")],
)
def test_bad_credentials_are_rejected(token: str, code: str) -> None:
    store = TokenStore()
    with pytest.raises(AuthenticationError) as exc:
        store.verify(token, now=NOW)
    assert exc.value.code == code


@pytest.mark.safety
def test_an_expired_token_is_rejected() -> None:
    store = TokenStore()
    token, _ = store.issue("owner", Role.OWNER, {"home_001"}, ttl=timedelta(hours=1), now=NOW)
    store.verify(token, now=NOW)
    with pytest.raises(AuthenticationError) as exc:
        store.verify(token, now=NOW + timedelta(hours=2))
    assert exc.value.code == "TOKEN_EXPIRED"


@pytest.mark.safety
def test_a_revoked_token_stops_working_immediately() -> None:
    store = TokenStore()
    token, _ = store.issue("owner", Role.OWNER, {"home_001"}, now=NOW)
    assert store.revoke(token)
    with pytest.raises(AuthenticationError) as exc:
        store.verify(token, now=NOW)
    assert exc.value.code == "TOKEN_REVOKED"


@pytest.mark.safety
def test_revoking_a_subject_invalidates_all_of_its_tokens() -> None:
    # The response to a compromised account.
    store = TokenStore()
    tokens = [store.issue("owner", Role.OWNER, {"home_001"}, now=NOW)[0] for _ in range(3)]
    other, _ = store.issue("guest", Role.GUEST, {"home_001"}, now=NOW)

    assert store.revoke_subject("owner") == 3
    for token in tokens:
        with pytest.raises(AuthenticationError):
            store.verify(token, now=NOW)
    assert store.verify(other, now=NOW).subject == "guest"


def test_expired_tokens_can_be_purged() -> None:
    store = TokenStore()
    store.issue("a", Role.GUEST, {"home_001"}, ttl=timedelta(minutes=1), now=NOW)
    store.issue("b", Role.GUEST, {"home_001"}, ttl=timedelta(days=1), now=NOW)
    assert store.purge_expired(now=NOW + timedelta(hours=1)) == 1
    assert len(store) == 1


def test_tokens_are_unique_per_issue() -> None:
    store = TokenStore()
    issued = {store.issue("owner", Role.OWNER, {"home_001"}, now=NOW)[0] for _ in range(50)}
    assert len(issued) == 50


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        ("Bearer abc123", "abc123"),
        ("bearer abc123", "abc123"),
        ("Basic abc123", ""),
        ("abc123", ""),
        (None, ""),
        ("", ""),
    ],
)
def test_bearer_header_parsing(header: str | None, expected: str) -> None:
    assert bearer_token(header) == expected


@pytest.mark.safety
def test_the_safety_authority_guarantee_survives_optimised_bytecode() -> None:
    """`python -O` strips assert statements.

    The rule that no role holds ACT_SAFETY is enforced by a raise at import
    time, not an assert, so it cannot be optimised away in a production image
    built with -O.
    """
    import subprocess
    import sys

    program = (
        "from syltra_security import ROLE_PERMISSIONS, Permission;"
        "holders=[r for r,p in ROLE_PERMISSIONS.items() if Permission.ACT_SAFETY in p];"
        "print('HOLDERS:'+','.join(str(h) for h in holders))"
    )
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-O", "-c", program], capture_output=True, text=True, check=True
    )
    assert result.stdout.strip() == "HOLDERS:"


def test_the_module_uses_no_assert_for_its_safety_rule() -> None:
    import pathlib

    import syltra_security.authorization as module

    source = pathlib.Path(str(module.__file__)).read_text(encoding="utf-8")
    assert "raise RuntimeError" in source
    assert "\nassert " not in source
