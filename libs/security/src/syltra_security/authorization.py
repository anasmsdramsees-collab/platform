"""Roles, permissions and home-scoped authorization (spec §25.1).

Two ideas do the work here.

**Permissions are separated by consequence, not by convenience.** Spec §25.1
requires "separate permissions for comfort, security, and safety actions",
because the person who may dim a lamp is not automatically the person who may
unlock a door. `Permission` therefore splits action authority three ways, and
the split follows the `SafetyClass` a capability already declares.

**Home scope is checked before anything else.** Every principal is bound to the
homes it may see, and `authorize` refuses a foreign home before it even looks at
permissions — so a role misconfiguration can never become cross-household data
exposure.
"""

import hmac
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Final

from syltra_contracts.capability_definitions import get_definition
from syltra_contracts.enums import SafetyClass


class Permission(StrEnum):
    """What a principal may do, split by consequence."""

    READ_HOME = "READ_HOME"
    """See devices, contexts, recommendations and risk state."""
    READ_AUDIT = "READ_AUDIT"
    """See the audit trail — separate, because it reveals who did what."""
    APPROVE_RECOMMENDATION = "APPROVE_RECOMMENDATION"
    ACT_COMFORT = "ACT_COMFORT"
    """Lights, climate, covers, switches."""
    ACT_SECURITY = "ACT_SECURITY"
    """Locks, garage doors, cameras — deliberately not implied by comfort."""
    ACT_SAFETY = "ACT_SAFETY"
    """Valves, breakers, sirens. Held by the safety layer, not by people."""
    MANAGE_MODELS = "MANAGE_MODELS"
    MANAGE_POLICY = "MANAGE_POLICY"
    MANAGE_PRIVACY = "MANAGE_PRIVACY"
    """Consent, export and deletion (spec §26)."""
    MANAGE_USERS = "MANAGE_USERS"
    """Invite a person, change their role, revoke their access.

    Separate from MANAGE_POLICY because they answer different questions.
    Policy is what the household allows; this is who the household is. Somebody
    who may tune a comfort threshold has no business granting a stranger a key.
    """
    ACKNOWLEDGE_SAFETY = "ACKNOWLEDGE_SAFETY"
    """Acknowledge a confirmed hazard and close its case once it has cleared.

    Deliberately *not* ACT_SAFETY. This permission removes a case from the
    screen; it commands no actuator. The distinction is the whole reason the
    Safety Operator role can exist without breaking invariants 6, 13 and 18:
    somebody has to be able to say "the leak is dealt with", and that is a
    different act from opening a gas valve.
    """
    MANAGE_AUTOMATIONS = "MANAGE_AUTOMATIONS"
    """Write, enable and disable the household's own automations.

    Separate from ACT_COMFORT because the two are different in time. Acting on
    comfort changes something now, and a person sees the result. Writing an
    automation changes what happens later, repeatedly, when nobody is watching —
    a guest who may turn a light on should not be able to leave behind a rule
    that turns it on every night.
    """
    READ_DIAGNOSTICS = "READ_DIAGNOSTICS"
    """Entity ids, protocol details, signal and firmware internals.

    Separate from READ_HOME because UI guidelines §17.7 draws the line there:
    "hide low-level identifiers from ordinary users and expose them to
    authorized technicians". A household member seeing the living-room
    temperature has no reason to see the integration's entity id, and exposing
    it invites support requests phrased in terms the platform does not promise
    to keep stable.
    """


class Role(StrEnum):
    OWNER = "OWNER"
    ADULT = "ADULT"
    CHILD = "CHILD"
    GUEST = "GUEST"
    INSTALLER = "INSTALLER"
    SAFETY_OPERATOR = "SAFETY_OPERATOR"
    """The person a confirmed hazard is escalated to.

    Assignable only by an Owner (enforced in the user directory, not here).
    Holds no authority over any device: a confirmed gas hazard closes its own
    valve deterministically, and reopening it is a physical act performed by
    someone who has found out why it leaked. What this role adds is a named,
    auditable person who can say the incident is over.
    """
    SERVICE = "SERVICE"
    """A platform service acting on its own behalf, not a person."""


ROLE_PERMISSIONS: Final[dict[Role, frozenset[Permission]]] = {
    Role.OWNER: frozenset(
        {
            Permission.READ_HOME,
            Permission.READ_AUDIT,
            Permission.APPROVE_RECOMMENDATION,
            Permission.ACT_COMFORT,
            Permission.ACT_SECURITY,
            Permission.MANAGE_MODELS,
            Permission.MANAGE_POLICY,
            Permission.MANAGE_PRIVACY,
            Permission.READ_DIAGNOSTICS,
            Permission.MANAGE_AUTOMATIONS,
            Permission.MANAGE_USERS,
            Permission.ACKNOWLEDGE_SAFETY,
        }
    ),
    Role.ADULT: frozenset(
        {
            Permission.READ_HOME,
            Permission.APPROVE_RECOMMENDATION,
            Permission.ACT_COMFORT,
            Permission.ACT_SECURITY,
            Permission.MANAGE_AUTOMATIONS,
        }
    ),
    # A child may see the home and adjust comfort, but not unlock doors,
    # approve automation, or read who did what.
    Role.CHILD: frozenset({Permission.READ_HOME, Permission.ACT_COMFORT}),
    Role.GUEST: frozenset({Permission.READ_HOME}),
    # An installer commissions hardware; they are not a household member and
    # cannot read the audit trail or operate security devices.
    Role.INSTALLER: frozenset(
        {Permission.READ_HOME, Permission.ACT_COMFORT, Permission.READ_DIAGNOSTICS}
    ),
    # Sees everything a household member sees, plus the audit trail, and
    # commands nothing. The audit access is the point: an incident is reviewed
    # by reading what happened, not by pressing anything.
    Role.SAFETY_OPERATOR: frozenset(
        {
            Permission.READ_HOME,
            Permission.READ_AUDIT,
            Permission.READ_DIAGNOSTICS,
            Permission.ACKNOWLEDGE_SAFETY,
        }
    ),
    Role.SERVICE: frozenset({Permission.READ_HOME}),
}

# ACT_SAFETY appears in no role — including SAFETY_OPERATOR, which is named
# after safety and holds none of it. Life-safety actuators are commanded by
# deterministic rules through the Safety Governor, never by a person holding a
# permission (safety invariants 6, 13, 18).
#
# Raised, not asserted: `python -O` strips assert statements, and a safety
# guarantee that disappears under an optimisation flag is not a guarantee.
_ROLES_WITH_SAFETY_AUTHORITY = [
    role
    for role, permissions in ROLE_PERMISSIONS.items()
    if Permission.ACT_SAFETY in permissions
]
if _ROLES_WITH_SAFETY_AUTHORITY:  # pragma: no cover - guarded by tests
    _msg = (
        "no role may hold ACT_SAFETY; life-safety actuators are commanded by "
        f"deterministic safety rules only. Offending roles: {_ROLES_WITH_SAFETY_AUTHORITY}"
    )
    raise RuntimeError(_msg)


_SAFETY_CLASS_PERMISSION: Final[dict[SafetyClass, Permission]] = {
    SafetyClass.NON_CRITICAL: Permission.ACT_COMFORT,
    SafetyClass.COMFORT: Permission.ACT_COMFORT,
    SafetyClass.SECURITY_SENSITIVE: Permission.ACT_SECURITY,
    SafetyClass.SAFETY_RELATED: Permission.ACT_SAFETY,
    SafetyClass.LIFE_SAFETY_CRITICAL: Permission.ACT_SAFETY,
}


def permission_for_capability(capability: str) -> Permission:
    """The permission required to command a capability.

    Derived from the capability's declared safety class rather than a separate
    list, so a new capability cannot be added without inheriting the right
    authority requirement.
    """
    return _SAFETY_CLASS_PERMISSION[get_definition(capability).safety_class]


@dataclass(frozen=True)
class Principal:
    """An authenticated caller, bound to the homes it may address."""

    subject: str
    role: Role
    home_ids: frozenset[str]
    display_name: str | None = None
    permissions: frozenset[Permission] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not self.permissions:
            object.__setattr__(self, "permissions", ROLE_PERMISSIONS[self.role])

    def may(self, permission: Permission) -> bool:
        return permission in self.permissions

    def sees(self, home_id: str) -> bool:
        return home_id in self.home_ids


class AuthorizationError(PermissionError):
    """Raised when a principal may not do what it asked."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code


def authorize(principal: Principal, home_id: str, permission: Permission) -> None:
    """Check home scope first, then permission.

    Order matters. Reporting "insufficient permission" for a home the caller
    cannot see would confirm that the home exists — a small leak, but a real
    one across households.
    """
    if not principal.sees(home_id):
        msg = f"{principal.subject} is not a member of {home_id}"
        raise AuthorizationError("HOME_NOT_FOUND", msg)
    if not principal.may(permission):
        msg = f"role {principal.role.value} does not hold {permission.value}"
        raise AuthorizationError("INSUFFICIENT_PERMISSION", msg)


def authorize_capability(principal: Principal, home_id: str, capability: str) -> None:
    """Authorize a manual command against a capability."""
    authorize(principal, home_id, permission_for_capability(capability))


def constant_time_equals(a: str, b: str) -> bool:
    """Compare secrets without leaking length or content through timing."""
    return hmac.compare_digest(a.encode(), b.encode())
