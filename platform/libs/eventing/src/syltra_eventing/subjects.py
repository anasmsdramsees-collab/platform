"""NATS subject builders (spec §12).

Subjects are dot-delimited; embedded identifiers must therefore never contain
NATS-reserved characters. ``sanitize_token`` maps arbitrary external
identifiers (e.g. Home Assistant entity ids like ``sensor.kitchen``) onto a
single safe token, deterministically.
"""

import re

_UNSAFE = re.compile(r"[.\s*>]+")


def sanitize_token(identifier: str) -> str:
    """Deterministically map an external identifier to a NATS-safe token.

    Rejects identifiers that carry no alphanumeric content: those would all
    collapse onto the same placeholder token and route distinct devices onto
    one subject.
    """
    token = _UNSAFE.sub("_", identifier.strip())
    if not any(c.isalnum() for c in token):
        msg = f"identifier {identifier!r} cannot form a NATS subject token"
        raise ValueError(msg)
    return token


def raw_device_subject(home_id: str, device_id: str) -> str:
    return f"syltra.raw.home.{sanitize_token(home_id)}.device.{sanitize_token(device_id)}"


def normalized_device_subject(home_id: str, device_id: str) -> str:
    return f"syltra.normalized.home.{sanitize_token(home_id)}.device.{sanitize_token(device_id)}"


def twin_updated_subject(home_id: str) -> str:
    return f"syltra.twin.home.{sanitize_token(home_id)}.updated"


def context_updated_subject(home_id: str) -> str:
    return f"syltra.context.home.{sanitize_token(home_id)}.updated"


def recommendation_subject(home_id: str) -> str:
    return f"syltra.ai.home.{sanitize_token(home_id)}.recommendation"


def risk_state_subject(home_id: str) -> str:
    return f"syltra.risk.home.{sanitize_token(home_id)}.state"


def policy_decision_subject(home_id: str) -> str:
    return f"syltra.policy.home.{sanitize_token(home_id)}.decision"


def action_request_subject(home_id: str) -> str:
    return f"syltra.action.home.{sanitize_token(home_id)}.request"


def action_result_subject(home_id: str) -> str:
    return f"syltra.action.home.{sanitize_token(home_id)}.result"


def feedback_subject(home_id: str) -> str:
    return f"syltra.feedback.home.{sanitize_token(home_id)}.recorded"


def system_health_subject(hub_id: str) -> str:
    return f"syltra.system.hub.{sanitize_token(hub_id)}.health"


def deadletter_subject(service: str) -> str:
    return f"syltra.deadletter.{sanitize_token(service)}"
