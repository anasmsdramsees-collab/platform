"""WCAG contrast maths and the Phase UI-0 acceptance criteria (guidelines §22, §26).

Two of the four UI-0 acceptance criteria are enforced here:

- "token contrast checks pass" — every visible pair, in both themes;
- "no feature component contains hardcoded brand color" — the design system is
  the only place a hex may appear.

The third ("Arabic and English direction switch works") lives in the RTL tests,
and the fourth ("themes work without layout changes") is enforced by the token
parity test below: a theme may change colour and nothing else.
"""

import json
import re
from pathlib import Path

import pytest
from syltra_design_tokens import (
    LARGE_TEXT_RATIO,
    NORMAL_TEXT_RATIO,
    ContrastError,
    audit_all,
    audit_theme,
    brand_colours,
    contrast_ratio,
    load_tokens,
    parse_hex,
    relative_luminance,
    repo_root_from,
    required_ratio,
)

REPO_ROOT = repo_root_from(Path(__file__))
DESIGN_SYSTEM = REPO_ROOT / "apps" / "local-console" / "src" / "design-system"


# ── the formula ──


def test_black_and_white_are_the_extremes() -> None:
    # The two anchors of the scale: if these are wrong, everything is.
    assert contrast_ratio("#FFFFFF", "#000000") == pytest.approx(21.0)
    assert contrast_ratio("#FFFFFF", "#FFFFFF") == pytest.approx(1.0)


def test_contrast_is_symmetric() -> None:
    # The ratio describes a pair, not a direction.
    assert contrast_ratio("#2BC4D9", "#0A0D10") == pytest.approx(
        contrast_ratio("#0A0D10", "#2BC4D9")
    )


def test_luminance_matches_the_wcag_anchors() -> None:
    assert relative_luminance("#000000") == pytest.approx(0.0)
    assert relative_luminance("#FFFFFF") == pytest.approx(1.0)
    # Mid grey is not 0.5: the transfer function is not linear.
    assert relative_luminance("#808080") == pytest.approx(0.2159, abs=1e-4)


def test_shorthand_hex_expands() -> None:
    assert parse_hex("#FFF") == (255, 255, 255)
    assert parse_hex("2BC4D9") == (0x2B, 0xC4, 0xD9)


@pytest.mark.parametrize("bad", ["#12", "#GGGGGG", "", "rgb(0,0,0)"])
def test_unparseable_colours_are_rejected(bad: str) -> None:
    # A typo in a token must fail loudly, not silently score as black.
    with pytest.raises(ContrastError):
        parse_hex(bad)


def test_large_text_uses_the_relaxed_bar_only_when_it_qualifies() -> None:
    assert required_ratio() == NORMAL_TEXT_RATIO
    assert required_ratio(16.0) == NORMAL_TEXT_RATIO
    assert required_ratio(24.0) == LARGE_TEXT_RATIO
    assert required_ratio(20.0, bold=True) == LARGE_TEXT_RATIO
    # 18px bold is below the 18.66px (14pt) threshold and stays at 4.5:1.
    assert required_ratio(18.0, bold=True) == NORMAL_TEXT_RATIO


# ── the acceptance criterion: token contrast checks pass ──


@pytest.mark.parametrize("theme", ["dark", "light"])
def test_every_token_pair_meets_its_bar(theme: str) -> None:
    audit = audit_theme(load_tokens(REPO_ROOT), theme)
    assert audit.checks, "the audit enumerated nothing, so it proves nothing"
    failures = [failure.describe() for failure in audit.failures]
    assert not failures, "\n" + "\n".join(failures)


def test_both_themes_are_audited_to_the_same_depth() -> None:
    # A theme must not pass by being checked less thoroughly than the other.
    dark, light = audit_all(REPO_ROOT)
    assert [c.name for c in dark.checks] == [c.name for c in light.checks]


def test_status_colours_are_readable_as_text_in_both_themes() -> None:
    # §6.5: "every semantic color must include text and icon support". A status
    # hue that only works as a fill is not enough.
    for audit in audit_all(REPO_ROOT):
        status = [c for c in audit.checks if c.name.startswith("status-")]
        assert len(status) >= 12, audit.theme
        assert all(c.required == NORMAL_TEXT_RATIO for c in status)
        assert all(c.passes for c in status)


def test_the_focus_ring_is_visible_on_every_theme() -> None:
    # §22: focus must be visible, which means measurable, not merely present.
    for audit in audit_all(REPO_ROOT):
        rings = [c for c in audit.checks if c.name.startswith("focus-ring")]
        assert rings, audit.theme
        assert all(c.passes for c in rings)


# ── the acceptance criterion: themes work without layout changes ──


def test_the_two_themes_define_exactly_the_same_tokens() -> None:
    # Switching theme may change colour and nothing else. If one theme carried
    # a token the other lacked, a component would fall back mid-switch.
    tokens = load_tokens(REPO_ROOT)
    dark = {k for k in tokens["theme"]["dark"] if not k.startswith("_")}
    light = {k for k in tokens["theme"]["light"] if not k.startswith("_")}
    assert dark == light


def test_themes_carry_colour_only() -> None:
    # No spacing, size or font token may live in a theme, or the layout would
    # shift when the theme does.
    tokens = load_tokens(REPO_ROOT)
    for theme, palette in tokens["theme"].items():
        for name, value in palette.items():
            if name.startswith("_"):
                continue
            assert re.fullmatch(r"#[0-9A-Fa-f]{3,8}", value), f"{theme}.{name} = {value!r}"


# ── the acceptance criterion: no hardcoded brand colour outside the tokens ──


def _stylesheets() -> list[Path]:
    return sorted(
        path
        for path in DESIGN_SYSTEM.rglob("*.css")
        if "tokens" not in path.parts and "themes" not in path.parts
    )


HEX = re.compile(r"#[0-9A-Fa-f]{3,8}\b")


def test_the_shared_stylesheets_hold_no_hex_colours() -> None:
    # Every colour must come through a token, so a palette change is one edit.
    offenders = {
        path.relative_to(REPO_ROOT).as_posix(): HEX.findall(path.read_text(encoding="utf-8"))
        for path in _stylesheets()
    }
    assert not {k: v for k, v in offenders.items() if v}


def test_generated_css_carries_every_brand_colour() -> None:
    # The converse guard: the tokens must actually reach CSS, or the stylesheets
    # would be hex-free because they are colour-free.
    tokens = load_tokens(REPO_ROOT)
    generated = "\n".join(
        (DESIGN_SYSTEM / name).read_text(encoding="utf-8")
        for name in ("tokens/tokens.css", "themes/dark-theme.css", "themes/light-theme.css")
    ).upper()
    missing = sorted(colour for colour in brand_colours(tokens) if colour not in generated)
    assert not missing


# ── the generated CSS must not drift from its source ──


def test_generated_css_matches_tokens_json() -> None:
    # Same guard the JSON Schemas use: the checked-in output is regenerated and
    # compared, so nobody can hand-edit a generated file and have it stick.
    import sys

    sys.path.insert(0, str(REPO_ROOT / "infrastructure" / "scripts"))
    from build_tokens import render_all

    stale = [
        path.relative_to(REPO_ROOT).as_posix()
        for path, content in render_all(REPO_ROOT).items()
        if path.read_text(encoding="utf-8") != content
    ]
    assert not stale, f"run `make tokens`: {stale}"


def test_tokens_json_is_valid_and_complete() -> None:
    tokens = load_tokens(REPO_ROOT)
    required = {
        "meta",
        "brand",
        "status",
        "theme",
        "space",
        "radius",
        "elevation",
        "typography",
        "motion",
        "layout",
        "control",
        "density",
    }
    assert required <= set(tokens)
    # Round-trips: the file the build reads is the file the audit reads.
    raw = (DESIGN_SYSTEM / "tokens" / "tokens.json").read_text(encoding="utf-8")
    assert json.loads(raw) == tokens
