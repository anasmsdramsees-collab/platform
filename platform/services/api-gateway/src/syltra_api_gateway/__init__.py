"""SYLTRA Local API Gateway (spec §14.9, §21).

The only publicly exposed SYLTRA service. Authenticated, home-scoped, and
composed from in-process read models so no endpoint can leak a broker subject,
a stream sequence or a database shape.
"""

from syltra_api_gateway.api import API_VERSION, create_app
from syltra_api_gateway.platform import Platform
from syltra_api_gateway.translations import (
    REASON_CODES,
    SUPPORTED_LOCALES,
    is_rtl,
    negotiate_locale,
    translate_reason,
    translate_reasons,
)

__all__ = [
    "API_VERSION",
    "REASON_CODES",
    "SUPPORTED_LOCALES",
    "Platform",
    "create_app",
    "is_rtl",
    "negotiate_locale",
    "translate_reason",
    "translate_reasons",
]
