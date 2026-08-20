"""Phase UI-0 acceptance: the design system's structural guarantees.

The contrast bars are verified in `libs/design-tokens`; this file covers the
guarantees that live in the CSS itself — bidirectional layout, the accessibility
baseline, and the brand rules the guidelines state as absolutes (§0, §5.4, §6.2).

These are text-level checks, which is the honest limit of a no-build-step design
system: they prove the rules are written into the stylesheets, not that a
browser paints them. Guidelines §28 keeps the browser checks (screen reader,
200% zoom, RTL walkthrough) as manual tests, and they are recorded there.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
DESIGN_SYSTEM = ROOT / "apps" / "local-console" / "src" / "design-system"
FOUNDATION = DESIGN_SYSTEM / "foundation.css"
PRIMITIVES = DESIGN_SYSTEM / "primitives.css"
SHELL = DESIGN_SYSTEM / "shell.css"
DOMAIN = DESIGN_SYSTEM / "domain.css"

AUTHORED = [FOUNDATION, PRIMITIVES, SHELL, DOMAIN]
GENERATED = sorted(
    path
    for path in DESIGN_SYSTEM.rglob("*.css")
    if path.parent.name in {"tokens", "themes", "typography"}
)


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _without_comments(css: str) -> str:
    """Strip /* … */ so a rule quoted in prose cannot satisfy a check."""
    return re.sub(r"/\*.*?\*/", " ", css, flags=re.DOTALL)


ALL_CSS = "\n".join(_text(path) for path in [*AUTHORED, *GENERATED])
AUTHORED_CODE = "\n".join(_without_comments(_text(path)) for path in AUTHORED)


# ── Arabic RTL foundation (§10) ──


PHYSICAL = re.compile(
    r"(?<![\w-])("
    r"margin-(?:left|right)|padding-(?:left|right)|border-(?:left|right)(?:-\w+)?|"
    r"text-align:\s*(?:left|right)|float:\s*(?:left|right)|"
    r"(?:^|[\s{;])(?:left|right):\s"
    r")",
    re.MULTILINE,
)


@pytest.mark.parametrize("path", AUTHORED, ids=lambda p: p.name)
def test_layout_is_written_in_logical_properties_only(path: Path) -> None:
    # §10.1: Arabic is genuine mirroring from dir="rtl", not a second
    # stylesheet. A single physical property is a bug that only shows in Arabic.
    found = PHYSICAL.findall(_without_comments(_text(path)))
    assert not found, f"{path.name} uses physical properties: {sorted(set(found))}"


def test_direction_switching_needs_no_second_stylesheet() -> None:
    # The only [dir=…] rules that may exist are the deliberate exceptions:
    # icon mirroring and anything genuinely direction-specific.
    selectors = re.findall(r"\[dir=\"(\w+)\"\][^{]*", AUTHORED_CODE)
    assert selectors, "direction handling is missing entirely"
    assert set(selectors) <= {"rtl", "ltr"}


def test_directional_icons_mirror_and_universal_icons_never_do() -> None:
    # §10.2: arrows and chevrons mirror; power, play, check, warning and the
    # brand marks must not.
    assert '[dir="rtl"] .icon-directional' in AUTHORED_CODE
    assert re.search(r"\.icon-universal\s*\{[^}]*transform:\s*none\s*!important", AUTHORED_CODE)


def test_identifiers_and_numbers_are_direction_isolated() -> None:
    # §10.2: an entity id or a meter reading must not reorder inside an Arabic
    # sentence.
    for selector in (".identifier", ".numeric"):
        block = re.search(rf"{re.escape(selector)}\b[^{{]*\{{([^}}]*)\}}", AUTHORED_CODE)
        assert block, selector
        assert "unicode-bidi: isolate" in block.group(1)
    assert re.search(r"\.identifier[^{]*\{[^}]*direction:\s*ltr", AUTHORED_CODE)


def test_charts_stay_chronologically_left_to_right() -> None:
    # §10.2: time runs the same way in both languages; only the labels localize.
    assert re.search(r"\.chart-canvas\s*\{[^}]*direction:\s*ltr", AUTHORED_CODE)


def test_arabic_gets_its_own_family_and_line_height() -> None:
    # §7.3: IBM Plex Sans Arabic, with more leading than the Latin equivalent.
    typography = _text(DESIGN_SYSTEM / "typography" / "typography.css")
    assert '[lang="ar"]' in typography
    assert "--line-height-factor" in typography
    assert '[lang="ar"]' in AUTHORED_CODE
    assert "--font-arabic" in AUTHORED_CODE


# ── accessibility baseline (§22) ──


def test_keyboard_focus_is_always_visible() -> None:
    # §22: focus is never removed. `outline: none` anywhere is a failure, even
    # when something else is drawn in its place, because the replacement is not
    # guaranteed under forced colors.
    assert ":focus-visible" in AUTHORED_CODE
    assert "--focus-ring" in AUTHORED_CODE
    assert not re.search(r"outline:\s*(none|0)\b", AUTHORED_CODE)


def test_interactive_targets_carry_a_minimum_size() -> None:
    # §12.1, §22: 44px is the SYLTRA default, above the 24px WCAG floor.
    assert "--control-height-minimum" in AUTHORED_CODE
    assert re.search(r"min-block-size:\s*var\(--control-height-minimum\)", AUTHORED_CODE)


def test_reduced_motion_is_honoured() -> None:
    # §19, §22: animation is an enhancement and must be switchable off.
    motion = _text(DESIGN_SYSTEM / "tokens" / "motion.css")
    assert "@media (prefers-reduced-motion: reduce)" in motion
    assert "transition-duration: 1ms !important" in motion


def test_forced_colors_keeps_boundaries_visible() -> None:
    # §22 manual tests: Windows high contrast replaces every colour, so
    # anything that carried meaning through colour alone disappears.
    assert "@media (forced-colors: active)" in AUTHORED_CODE
    assert "CanvasText" in AUTHORED_CODE


def test_a_skip_link_and_a_screen_reader_class_exist() -> None:
    assert ".skip-link" in AUTHORED_CODE
    assert ".sr-only" in AUTHORED_CODE


def test_advisory_confirmed_and_shadow_differ_by_more_than_colour() -> None:
    # The single most important distinction in the product (§15), and the one
    # most likely to be reduced to a colour. Each gets its own border style, so
    # the three remain distinguishable in greyscale and under forced colors.
    styles = {}
    for variant in ("advisory", "confirmed", "shadow"):
        block = re.search(rf"\.badge--{variant}\b[^{{]*\{{([^}}]*)\}}", AUTHORED_CODE)
        assert block, variant
        found = re.search(r"border-style:\s*(\w+)", block.group(1))
        styles[variant] = found.group(1) if found else "solid"
    assert len(set(styles.values())) == 3, styles


def test_the_console_uses_the_shared_badge_rather_than_its_own() -> None:
    # The console defined a badge that separated advisory from confirmed by
    # colour alone. One implementation, in the design system, or the rule holds
    # in the catalogue and fails in the product.
    # The console no longer has a stylesheet at all, so there is nowhere for a
    # competing badge to live.
    assert not (ROOT / "apps" / "local-console" / "static" / "console.css").exists()
    console_js = _text(ROOT / "apps" / "local-console" / "static" / "console.js")
    # The console builds badges through one helper, so the check is that the
    # helper emits design-system modifiers and that every variant it is handed
    # is one the design system actually defines. A typo'd variant would
    # otherwise render an unstyled badge that still reads as a badge.
    assert "badge badge--${variant}" in console_js
    defined = set(re.findall(r"\.badge--([a-z]+)", _text(PRIMITIVES)))
    used = set(re.findall(r'badge\("([a-z]+)"', console_js))
    assert used, "the console renders no badges at all"
    assert used <= defined, sorted(used - defined)


def test_status_is_never_carried_by_colour_alone() -> None:
    # §6.5, §22: every badge pairs its colour with a shape or a border style,
    # so the state survives both colour blindness and forced colors.
    badge = re.search(r"\.badge\b[^{]*\{[^}]*\}", AUTHORED_CODE)
    assert badge
    assert re.search(r"\.badge[^{]*::before[^{]*\{", AUTHORED_CODE), "no non-colour shape cue"
    assert re.search(r"\.badge--advisory[^{]*\{[^}]*border-style:\s*dashed", AUTHORED_CODE)


# ── brand rules the guidelines state as absolutes ──


def test_green_is_semantic_only_and_never_a_brand_colour() -> None:
    # §6.2: "green appears in the status scale and nowhere else".
    import json

    tokens = json.loads(_text(DESIGN_SYSTEM / "tokens" / "tokens.json"))
    brand_hexes = []
    for value in tokens["brand"].values():
        if isinstance(value, dict):
            brand_hexes += [v for k, v in value.items() if not k.startswith("_")]
    for hex_value in brand_hexes:
        red, green, blue = (int(hex_value[i : i + 2], 16) for i in (1, 3, 5))
        assert not (green > red + 24 and green > blue + 24), f"{hex_value} is a green brand colour"


def test_the_console_never_names_home_assistant() -> None:
    # §5.4, and the platform rule that Home Assistant is an embedded runtime the
    # user never sees. A CSS class or comment leaking the name is a leak.
    assert not re.search(r"home[\s_-]?assistant", ALL_CSS, re.IGNORECASE)
    assert not re.search(r"\bhass\b|\bha-", ALL_CSS, re.IGNORECASE)


def test_product_names_use_the_mandated_spelling() -> None:
    # §5.4: "SYLTRA" and "SILA", exactly.
    for wrong in ("Syltra", "SYLTRA Smart Home", "Sila", "SYLA"):
        assert wrong not in ALL_CSS


def test_the_consumer_app_icon_is_not_referenced_by_the_platform() -> None:
    # §5.1: the consumer app icon is out of scope for the platform surface.
    assert "syltra-app-icon" not in ALL_CSS


# ── every token a stylesheet references must exist ──


DEFINITION = re.compile(r"(--[a-z0-9-]+)\s*:")
REFERENCE = re.compile(r"var\((--[a-z0-9-]+)")


def _defined_tokens() -> set[str]:
    names: set[str] = set()
    for path in GENERATED:
        names |= set(DEFINITION.findall(_text(path)))
    return names


@pytest.mark.parametrize(
    "path",
    [*AUTHORED, Path("apps/local-console/static/catalogue/catalogue.css")],
    ids=lambda p: p.name,
)
def test_every_referenced_token_is_defined(path: Path) -> None:
    # A typo in a var() name is silent: the property falls back to its initial
    # value and the component looks *nearly* right. This is the only cheap way
    # to catch it. Fallback values inside var() are still checked, because a
    # fallback that is always used is a token that never existed.
    resolved = path if path.is_absolute() else ROOT / path
    referenced = set(REFERENCE.findall(_text(resolved)))
    defined = _defined_tokens()
    # Density tokens are declared under [data-density], and the theme tokens
    # under the theme selectors; both are in the generated set already.
    missing = sorted(name for name in referenced if name not in defined)
    assert not missing, f"{resolved.name} references undefined tokens: {missing}"


# ── reflow: no content may be lost at 200% zoom (§22, WCAG 1.4.10) ──


def test_tables_live_in_a_scroll_container() -> None:
    # A device table is wider than a narrow viewport can hold. Without the
    # wrapper it is clipped by its card and the far columns become unreachable
    # — worse than a scrollbar, because nothing signals that they exist.
    assert re.search(r"\.table-scroll\s*\{[^}]*overflow-x:\s*auto", AUTHORED_CODE)
    catalogue = _text(ROOT / "apps" / "local-console" / "static" / "catalogue" / "index.html")
    for match in re.finditer(r'<table class="table"', catalogue):
        before = catalogue[: match.start()]
        assert 'class="table-scroll' in before.rsplit("<div", 1)[-1], (
            "a .table is not wrapped in .table-scroll"
        )


def test_a_scrollable_region_is_reachable_by_keyboard() -> None:
    # WCAG 2.1.1: a region that only a mouse can scroll is a region a keyboard
    # user cannot read.
    catalogue = _text(ROOT / "apps" / "local-console" / "static" / "catalogue" / "index.html")
    for match in re.finditer(r'<div class="table-scroll[^"]*"([^>]*)>', catalogue):
        attributes = match.group(1)
        assert 'tabindex="0"' in attributes
        assert "aria-label=" in attributes


def test_the_skip_link_is_fixed_to_the_viewport() -> None:
    # An absolutely positioned skip link resolves against the initial containing
    # block, so once the page has scrolled it is focusable but off-screen —
    # which is the exact failure the skip link exists to prevent.
    assert re.search(r"\.skip-link\s*\{[^}]*position:\s*fixed", AUTHORED_CODE)


# ── the catalogue must not silently omit a component ──


CATALOGUE = ROOT / "apps" / "local-console" / "static" / "catalogue" / "index.html"


def test_the_catalogue_renders_every_component_the_system_defines() -> None:
    # A catalogue that documents most of the design system is worse than none:
    # it looks like a complete inventory. Whatever primitives.css styles, the
    # catalogue shows — so adding a component without a specimen fails here.
    source = "".join(_without_comments(_text(p)) for p in (PRIMITIVES, SHELL, DOMAIN))
    classes = set(re.findall(r"^\.([a-z][a-z0-9_-]*)", source, re.M))
    catalogue = _text(CATALOGUE)
    rendered = set(re.findall(r'class="([^"]+)"', catalogue))
    shown = {name for group in rendered for name in group.split()}
    # `__element` classes are structural parts of a component, not components,
    # and the pinned-header modifier is a usage choice rather than a state.
    expected = {name for name in classes if "__" not in name}
    missing = sorted(expected - shown)
    assert not missing, f"components with no specimen: {missing}"


def test_the_catalogue_can_switch_theme_direction_and_density() -> None:
    # UI-0 acceptance: themes and direction switch without a reload, and a
    # component that only survives one combination is not finished.
    catalogue = _text(CATALOGUE)
    for control in ("theme", "direction", "density"):
        assert f'id="{control}"' in catalogue
    script = _text(CATALOGUE.parent / "catalogue.js")
    assert 'setAttribute("data-theme"' in script
    assert 'setAttribute("dir"' in script
    assert 'setAttribute("data-density"' in script
    assert 'setAttribute("lang"' in script


def test_the_catalogue_builds_its_dom_without_innerhtml() -> None:
    # Same rule as the console: nothing is assembled from strings.
    script = _without_comments(_text(CATALOGUE.parent / "catalogue.js"))
    script = re.sub(r"^\s*//.*$", "", script, flags=re.M)
    assert "innerHTML" not in script
    assert "createElement" in script


def test_the_catalogue_measures_contrast_rather_than_asserting_it() -> None:
    # The page recomputes ratios from what the browser painted. That is an
    # independent implementation of the same WCAG formula verified in
    # `libs/design-tokens`, and the two agreeing is worth more than either.
    script = _text(CATALOGUE.parent / "catalogue.js")
    assert "0.2126" in script and "0.7152" in script and "0.0722" in script
    assert "1.055" in script and "12.92" in script


# ── §21 critical-action confirmation (UI-4 acceptance) ──


CRITICAL_SPECIMEN = "critical-confirm"


@pytest.mark.safety
def test_no_critical_action_is_one_click() -> None:
    # The console commands no actuators today, so this is about the pattern
    # being right before the first one is built. §21 requires an explicit
    # confirmation step, and the confirming control is styled as its own thing
    # rather than a primary button — a generic "OK" for a critical action is
    # named in the prohibited list.
    catalogue = _text(CATALOGUE)
    assert CRITICAL_SPECIMEN in catalogue
    block = catalogue[catalogue.index('class="critical-confirm"') :]
    block = block[: block.index('</div>\n\n          <div class="dispatch-progress"')]
    assert "btn--critical-confirm" in block
    # Cancel precedes the destructive control in the reading order.
    assert block.index("btn--secondary") < block.index("btn--critical-confirm")


@pytest.mark.safety
def test_the_critical_confirmation_shows_every_disclosure_section_twentyone_lists() -> None:
    catalogue = _text(CATALOGUE)
    block = catalogue[catalogue.index('class="critical-confirm"') :]
    block = block[: block.index("</section>")]
    for required in (
        "Current state",
        "Intended state",
        "Expected impact",
        "Required permission",
        "Reversible",
        "Reason",
    ):
        assert required in block, required
    # Target and location, and the dispatch/verification progress.
    assert "Utility room" in block
    assert "dispatch-progress" in block


@pytest.mark.safety
def test_the_prohibited_confirmation_patterns_are_absent() -> None:
    # §21 names eight. These are the ones a stylesheet or markup can betray.
    catalogue = _without_comments(_text(CATALOGUE))
    block = catalogue[catalogue.index('class="critical-confirm"') :]
    block = block[: block.index("</section>")]
    # The prose *below* the specimen names the prohibited patterns in order to
    # explain them. Searching it would flag the explanation as the offence —
    # the same trap as grepping a comment that says "never innerHTML".
    block = block[: block.index('<p class="type-caption">')]
    assert "swipe" not in block.lower(), "no swipe-only confirmation"
    assert "autofocus" not in block.lower(), "no preselected dangerous option"
    assert "checked" not in block.lower(), "no preselected dangerous option"
    assert ">OK<" not in block, "no generic OK for a critical confirmation"
    # Not colour alone: each dispatch step carries a data-state as well.
    assert 'data-state="done"' in block
    assert 'data-state="failed"' in block


def test_reversibility_is_marked_rather_than_being_one_row_of_four() -> None:
    # It is the fact a person most needs before deciding.
    assert ".reversible-no" in AUTHORED_CODE
    block = re.search(r"\.reversible-no\s*\{([^}]*)\}", AUTHORED_CODE)
    assert block
    assert "--status-critical" in block.group(1)
    assert "font-weight" in block.group(1)


# ── UI-6 hardening ──


def test_a_link_that_fills_a_table_cell_meets_the_minimum_target_size() -> None:
    # WCAG 2.2 §2.5.8 exempts links inline in a sentence. A link that *is* a
    # table cell's content is a discrete target, not an inline one, and was
    # rendering 22px tall — below the 24px minimum. Padding rather than a fixed
    # height, so a wrapped device name still grows.
    rule = re.search(r"\.table a,\s*\.detail-list a\s*\{([^}]*)\}", AUTHORED_CODE)
    assert rule, "no minimum-size rule for links in tables"
    body = rule.group(1)
    assert "min-block-size: var(--control-height-minimum)" in body
    assert "inline-flex" in body


def test_no_screen_skips_a_heading_level() -> None:
    # Four screens went straight from the page `h1` to an `h3` card title,
    # which leaves a screen-reader user navigating by heading with a gap where
    # a section should be. Each got the section heading it was missing.
    console = _text(ROOT / "apps" / "local-console" / "static" / "console.js")
    # The settings cards *are* the sections, so their titles are second level.
    settings = console[
        console.index("function renderSettings") : console.index("function settingRow")
    ]
    assert 'el("h3"' not in settings, "settings cards are sections, not subsections"
    assert 'el("h2", "card__title"' in settings
    # Every screen that renders a card grid or metric row introduces it.
    for renderer, heading in (
        ("renderRooms", "nav_rooms"),
        ("renderRoomDetail", "environment"),
        ("renderEnergy", "current_power"),
    ):
        body = console[console.index(f"function {renderer}") :]
        body = body[: body.index("\n}")]
        assert f'"type-section-title", t("{heading}")' in body, renderer
