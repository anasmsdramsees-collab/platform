"""SYLTRA local security: authentication, roles and home-scoped authorization.

Spec §25.1 requires least privilege and separate permissions for comfort,
security and safety actions. `ACT_SAFETY` deliberately belongs to no role:
life-safety actuators are commanded by deterministic rules through the Safety
Governor, never by a person holding a permission.
"""

from syltra_security.directory import (
    DEFAULT_EXPIRY,
    OWNER_APPOINTED,
    Membership,
    MembershipChange,
    MembershipRefused,
    UserDirectory,
)
from syltra_security.authorization import (
    ROLE_PERMISSIONS,
    AuthorizationError,
    Permission,
    Principal,
    Role,
    authorize,
    authorize_capability,
    constant_time_equals,
    permission_for_capability,
)
from syltra_security.tokens import (
    AuthenticationError,
    TokenRecord,
    TokenStore,
    bearer_token,
    hash_token,
)

__all__ = [
    "OWNER_APPOINTED",
    "DEFAULT_EXPIRY",
    "UserDirectory",
    "MembershipRefused",
    "MembershipChange",
    "Membership",
    "ROLE_PERMISSIONS",
    "AuthenticationError",
    "AuthorizationError",
    "Permission",
    "Principal",
    "Role",
    "TokenRecord",
    "TokenStore",
    "authorize",
    "authorize_capability",
    "bearer_token",
    "constant_time_equals",
    "hash_token",
    "permission_for_capability",
]
