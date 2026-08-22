"""SILA — the SYLTRA intelligent interaction layer (spec §14.10).

SILA explains, asks and collects answers. It does not decide and it does not
act: it holds no device gateway, and every mutating intent is routed through the
Policy and Safety Service. The boundary is a closed set of typed intents, so
free text never becomes an actuator call.
"""

from syltra_sila.intents import (
    MUTATING_INTENTS,
    READ_ONLY_INTENTS,
    SILA_VERSION,
    IntentType,
    SilaIntent,
    SilaResponse,
)
from syltra_sila.phrases import PHRASES, phrase
from syltra_sila.service import SilaRefused, SilaService

__all__ = [
    "MUTATING_INTENTS",
    "PHRASES",
    "READ_ONLY_INTENTS",
    "SILA_VERSION",
    "IntentType",
    "SilaIntent",
    "SilaRefused",
    "SilaResponse",
    "SilaService",
    "phrase",
]
