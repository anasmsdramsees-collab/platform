"""Closed vocabularies from the master build specification.

These enums are contracts: adding, renaming, or removing a member is a
schema change and requires a spec update plus a migration note.
"""

from enum import StrEnum


class SafetyClass(StrEnum):
    """Capability safety classes (spec §10.3)."""

    NON_CRITICAL = "NON_CRITICAL"
    COMFORT = "COMFORT"
    SECURITY_SENSITIVE = "SECURITY_SENSITIVE"
    SAFETY_RELATED = "SAFETY_RELATED"
    LIFE_SAFETY_CRITICAL = "LIFE_SAFETY_CRITICAL"


class PrivacyClass(StrEnum):
    """Data privacy classes (spec §26)."""

    PUBLIC = "PUBLIC"
    SYSTEM_INTERNAL = "SYSTEM_INTERNAL"
    HOUSEHOLD_PRIVATE = "HOUSEHOLD_PRIVATE"
    PERSONAL_SENSITIVE = "PERSONAL_SENSITIVE"
    SAFETY_CRITICAL = "SAFETY_CRITICAL"


class PolicyOutcome(StrEnum):
    """Policy and Safety Service decision outcomes (spec §14.6)."""

    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_USER_APPROVAL = "REQUIRE_USER_APPROVAL"
    PREPARE_ONLY = "PREPARE_ONLY"
    ESCALATE_TO_FIXED_SAFETY_RULE = "ESCALATE_TO_FIXED_SAFETY_RULE"


class RiskCategory(StrEnum):
    """Risk Engine case categories (spec §14.5)."""

    GAS = "GAS"
    SMOKE_FIRE = "SMOKE_FIRE"
    CARBON_MONOXIDE = "CARBON_MONOXIDE"
    WATER_LEAK = "WATER_LEAK"
    ELECTRICAL = "ELECTRICAL"
    TEMPERATURE = "TEMPERATURE"
    INTRUSION = "INTRUSION"
    DEVICE_FAILURE = "DEVICE_FAILURE"
    CONNECTIVITY = "CONNECTIVITY"


class RiskState(StrEnum):
    """Risk case lifecycle states (spec §14.5).

    AI services may only ever produce WATCH and PRE_ALERT; CONFIRMED and
    beyond require deterministic approved conditions (safety invariant 6).
    """

    NORMAL = "NORMAL"
    WATCH = "WATCH"
    PRE_ALERT = "PRE_ALERT"
    CONFIRMED = "CONFIRMED"
    ACTION_IN_PROGRESS = "ACTION_IN_PROGRESS"
    RECOVERY = "RECOVERY"
    CLOSED = "CLOSED"


class LearningMode(StrEnum):
    """Adaptive-learning lifecycle modes (spec §19.1).

    Homes progress strictly in order; no home may skip from OBSERVE to
    AUTHORIZED_AUTOMATION (spec §19.2).
    """

    DISABLED = "DISABLED"
    OBSERVE = "OBSERVE"
    SHADOW = "SHADOW"
    RECOMMEND = "RECOMMEND"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    AUTHORIZED_AUTOMATION = "AUTHORIZED_AUTOMATION"
    SUSPENDED = "SUSPENDED"
