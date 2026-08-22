"""SYLTRA design tokens: loading and WCAG contrast verification.

Phase UI-0 acceptance requires "token contrast checks pass". These are computed
from the WCAG 2.2 formulas rather than eyeballed, so a palette change that
breaks contrast fails the build.
"""

from syltra_design_tokens.contrast import (
    LARGE_TEXT_RATIO,
    NON_TEXT_RATIO,
    NORMAL_TEXT_RATIO,
    ContrastCheck,
    ContrastError,
    check,
    contrast_ratio,
    parse_hex,
    relative_luminance,
    required_ratio,
)
from syltra_design_tokens.tokens import (
    ThemeAudit,
    audit_all,
    audit_theme,
    brand_colours,
    load_tokens,
    repo_root_from,
)

__all__ = [
    "LARGE_TEXT_RATIO",
    "NON_TEXT_RATIO",
    "NORMAL_TEXT_RATIO",
    "ContrastCheck",
    "ContrastError",
    "ThemeAudit",
    "audit_all",
    "audit_theme",
    "brand_colours",
    "check",
    "contrast_ratio",
    "load_tokens",
    "parse_hex",
    "relative_luminance",
    "repo_root_from",
    "required_ratio",
]
