"""Risk levels, and the one rule that keeps a language model away from a valve.

The specification defines three levels. The platform already classifies every
capability by safety class, so the mapping is a translation rather than a second
opinion. A second opinion is exactly what must not exist here: two tables that
both claim to say whether unlocking a door is dangerous will disagree one day,
and the one nobody tested will be the one in force.
"""

from enum import StrEnum


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    FORBIDDEN = "FORBIDDEN"


#: Safety class as the platform declares it, mapped to what SELLA may do.
FROM_SAFETY_CLASS: dict[str, RiskLevel] = {
    "NON_CRITICAL": RiskLevel.LOW,
    "COMFORT": RiskLevel.LOW,
    "SECURITY_SENSITIVE": RiskLevel.HIGH,
    "SAFETY_RELATED": RiskLevel.FORBIDDEN,
    "LIFE_SAFETY_CRITICAL": RiskLevel.FORBIDDEN,
}


def risk_for_safety_class(safety_class: str) -> RiskLevel:
    """Unknown classes are FORBIDDEN, not LOW.

    A capability the platform adds tomorrow, that this table has not heard of,
    must fail closed. Defaulting to LOW would mean every new actuator arrives
    reachable by a voice command nobody reviewed.
    """
    return FROM_SAFETY_CLASS.get(safety_class, RiskLevel.FORBIDDEN)


def may_execute(
    level: RiskLevel, *, confirmed: bool, approved: bool, high_risk_enabled: bool
) -> bool:
    """Whether a tool at this level may run right now.

    `confirmed` is a spoken confirmation inside the session. `approved` is an
    approval from the application with a PIN or biometric. The two are not
    interchangeable: knowing a voice is not proof of identity, which §16 states
    and this function enforces.
    """
    if level is RiskLevel.FORBIDDEN:
        return False
    if level is RiskLevel.LOW:
        return True
    if level is RiskLevel.MEDIUM:
        return confirmed
    return approved and high_risk_enabled
