"""The enum vocabularies must match the master spec exactly — no drift."""

import pytest
from syltra_contracts import (
    LearningMode,
    PolicyOutcome,
    PrivacyClass,
    RiskCategory,
    RiskState,
    SafetyClass,
)

pytestmark = pytest.mark.contract


def test_safety_classes_match_spec_10_3() -> None:
    assert {m.value for m in SafetyClass} == {
        "NON_CRITICAL",
        "COMFORT",
        "SECURITY_SENSITIVE",
        "SAFETY_RELATED",
        "LIFE_SAFETY_CRITICAL",
    }


def test_privacy_classes_match_spec_26() -> None:
    assert {m.value for m in PrivacyClass} == {
        "PUBLIC",
        "SYSTEM_INTERNAL",
        "HOUSEHOLD_PRIVATE",
        "PERSONAL_SENSITIVE",
        "SAFETY_CRITICAL",
    }


def test_policy_outcomes_match_spec_14_6() -> None:
    assert {m.value for m in PolicyOutcome} == {
        "ALLOW",
        "DENY",
        "REQUIRE_USER_APPROVAL",
        "PREPARE_ONLY",
        "ESCALATE_TO_FIXED_SAFETY_RULE",
    }


def test_risk_categories_match_spec_14_5() -> None:
    assert {m.value for m in RiskCategory} == {
        "GAS",
        "SMOKE_FIRE",
        "CARBON_MONOXIDE",
        "WATER_LEAK",
        "ELECTRICAL",
        "TEMPERATURE",
        "INTRUSION",
        "DEVICE_FAILURE",
        "CONNECTIVITY",
    }


def test_risk_states_match_spec_14_5() -> None:
    assert {m.value for m in RiskState} == {
        "NORMAL",
        "WATCH",
        "PRE_ALERT",
        "CONFIRMED",
        "ACTION_IN_PROGRESS",
        "RECOVERY",
        "CLOSED",
    }


def test_learning_modes_match_spec_19_1() -> None:
    assert {m.value for m in LearningMode} == {
        "DISABLED",
        "OBSERVE",
        "SHADOW",
        "RECOMMEND",
        "APPROVAL_REQUIRED",
        "AUTHORIZED_AUTOMATION",
        "SUSPENDED",
    }


def test_enum_members_serialize_as_plain_strings() -> None:
    # StrEnum members must be usable directly in JSON payloads and subjects.
    assert f"{RiskState.WATCH}" == "WATCH"
    assert SafetyClass.COMFORT == "COMFORT"
