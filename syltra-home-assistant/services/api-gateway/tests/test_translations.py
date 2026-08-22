"""Translation coverage tests (spec §21, §28).

Phase 7 acceptance: reason codes are translated. The coverage test extracts
codes from the actual source rather than from a hand-kept list, so a new reason
code cannot ship untranslated.
"""

import ast
import pathlib

import pytest
from syltra_api_gateway.translations import (
    DEFAULT_LOCALE,
    REASON_CODES,
    SUPPORTED_LOCALES,
    is_rtl,
    negotiate_locale,
    translate_reason,
    translate_reasons,
    untranslated_codes,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]

# Codes assembled at runtime from a capability name, which the AST scan sees
# only as a fragment. Listed explicitly with the expansion they produce.
DYNAMIC_CODES = {
    "CERTIFIED_GAS_ALARM_ACTIVE",
    "CERTIFIED_SMOKE_ALARM_ACTIVE",
    "CERTIFIED_HEAT_ALARM_ACTIVE",
    "CERTIFIED_CO_ALARM_ACTIVE",
    "CERTIFIED_WATER_LEAK_ACTIVE",
    "GAS_ALARM_READING",
    "SMOKE_ALARM_READING",
    "HEAT_ALARM_READING",
    "CO_ALARM_READING",
    "TWIN_STATUS_STALE",
    "TWIN_STATUS_UNKNOWN",
}

# Fragments and non-reason values the scan picks up from f-strings and evidence
# dictionaries; none is ever emitted as a whole reason code.
_FRAGMENTS = {"CERTIFIED_", "_ACTIVE", "_READING", "TWIN_STATUS_", "SHADOW"}


def emitted_reason_codes() -> set[str]:
    """Extract every literal reason code from the platform source."""
    codes: set[str] = set()
    sources = list((REPO_ROOT / "services").rglob("src/**/*.py"))
    sources += list((REPO_ROOT / "libs").rglob("src/**/*.py"))
    for path in sources:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.keyword) and node.arg in {"reason_codes", "reason_code"}:
                codes |= _string_constants(node.value)
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "append"
                and isinstance(node.func.value, ast.Name)
                and "reason" in node.func.value.id
            ):
                for arg in node.args:
                    codes |= _string_constants(arg)
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in {"RuleVerdict", "ActionRefused", "InsufficientCapabilityData"}
            ):
                for arg in node.args:
                    codes |= _string_constants(arg)
    return {c for c in codes if c not in _FRAGMENTS}


def _string_constants(node: ast.AST) -> set[str]:
    found: set[str] = set()
    for sub in ast.walk(node):
        if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
            value = sub.value
            if value.isupper() and len(value) > 3:
                found.add(value)
    return found


# ── coverage ──


def test_every_emitted_reason_code_is_translated() -> None:
    missing = untranslated_codes(emitted_reason_codes())
    assert missing == set(), f"reason codes with no translation: {sorted(missing)}"


def test_dynamically_assembled_codes_are_translated() -> None:
    missing = untranslated_codes(DYNAMIC_CODES)
    assert missing == set(), f"dynamic reason codes with no translation: {sorted(missing)}"


def test_every_entry_covers_every_supported_locale() -> None:
    for code, entry in REASON_CODES.items():
        for locale in SUPPORTED_LOCALES:
            assert entry.get(locale), f"{code} has no {locale} translation"


def test_arabic_entries_actually_contain_arabic() -> None:
    # Guards against an entry that quietly copies the English text.
    for code, entry in REASON_CODES.items():
        arabic = entry["ar"]
        has_arabic = any("؀" <= ch <= "ۿ" for ch in arabic)
        assert has_arabic, f"{code} has no Arabic characters in its ar translation"


def test_arabic_and_english_differ() -> None:
    for code, entry in REASON_CODES.items():
        assert entry["ar"] != entry["en"], f"{code} has identical ar and en text"


# ── behaviour ──


def test_translation_returns_the_requested_locale() -> None:
    assert translate_reason("MOTION_DETECTED", "en") == "Motion detected"
    assert translate_reason("MOTION_DETECTED", "ar") == "تم رصد حركة"


def test_an_unknown_code_returns_itself_rather_than_raising() -> None:
    # A user seeing a raw identifier is cosmetic; an API failing mid-incident
    # because a new code is untranslated is not.
    assert translate_reason("SOME_FUTURE_CODE", "ar") == "SOME_FUTURE_CODE"


def test_an_unknown_locale_falls_back_to_english() -> None:
    assert translate_reason("MOTION_DETECTED", "fr") == "Motion detected"


def test_lists_are_translated_in_order() -> None:
    codes = ["MOTION_DETECTED", "QUIET_HOURS"]
    assert translate_reasons(codes, "en") == ["Motion detected", "Quiet hours"]
    assert len(translate_reasons(codes, "ar")) == 2


@pytest.mark.parametrize(
    ("header", "override", "expected"),
    [
        ("ar", None, "ar"),
        ("ar-SA,ar;q=0.9,en;q=0.8", None, "ar"),
        ("en-GB,en;q=0.9", None, "en"),
        ("fr-FR,fr;q=0.9", None, "en"),
        (None, None, "en"),
        ("en", "ar", "ar"),
        ("ar", "en", "en"),
        ("ar", "fr", "ar"),
    ],
)
def test_locale_negotiation(header: str | None, override: str | None, expected: str) -> None:
    assert negotiate_locale(header, override) == expected


def test_rtl_locales_are_identified() -> None:
    assert is_rtl("ar")
    assert not is_rtl("en")
    assert not is_rtl(DEFAULT_LOCALE)
