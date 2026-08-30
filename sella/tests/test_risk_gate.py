"""The gate that keeps a language model away from a valve."""

import pytest

from policies.risk import RiskLevel, may_execute, risk_for_safety_class


def test_a_capability_nobody_classified_is_forbidden() -> None:
    # The failure that matters: the platform adds a capability, this table has
    # not heard of it, and it must not arrive reachable.
    assert risk_for_safety_class("PLASMA_CUTTER") is RiskLevel.FORBIDDEN


@pytest.mark.parametrize(
    ("safety_class", "level"),
    [
        ("COMFORT", RiskLevel.LOW),
        ("NON_CRITICAL", RiskLevel.LOW),
        ("SECURITY_SENSITIVE", RiskLevel.HIGH),
        ("SAFETY_RELATED", RiskLevel.FORBIDDEN),
        ("LIFE_SAFETY_CRITICAL", RiskLevel.FORBIDDEN),
    ],
)
def test_the_platform_classes_map_the_way_the_spec_says(
    safety_class: str, level: RiskLevel
) -> None:
    assert risk_for_safety_class(safety_class) is level


def test_forbidden_stays_forbidden_even_when_everything_is_switched_on() -> None:
    assert not may_execute(
        RiskLevel.FORBIDDEN, confirmed=True, approved=True, high_risk_enabled=True
    )


def test_a_spoken_confirmation_is_not_an_approval() -> None:
    # §16: recognising a voice is not proof of identity. A HIGH action needs the
    # application, not a person saying "yes" to a speaker.
    assert not may_execute(RiskLevel.HIGH, confirmed=True, approved=False, high_risk_enabled=True)
    assert may_execute(RiskLevel.HIGH, confirmed=False, approved=True, high_risk_enabled=True)


def test_high_risk_is_unreachable_while_the_flag_is_off() -> None:
    assert not may_execute(RiskLevel.HIGH, confirmed=True, approved=True, high_risk_enabled=False)
