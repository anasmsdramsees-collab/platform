"""The wall panel's own front end.

The console's tests ask whether a screen is complete. These ask whether a
screen on a wall in somebody's hallway behaves like one: readable across a
room, pressable without looking, honest when it cannot reach the hub, and
impossible to use as a way into anything it should not reach.
"""

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
PANEL = ROOT / "apps" / "wall-panel" / "static"
JS = (PANEL / "panel.js").read_text(encoding="utf-8")
CSS = (PANEL / "panel.css").read_text(encoding="utf-8")
HTML = (PANEL / "index.html").read_text(encoding="utf-8")
I18N = json.loads((PANEL / "i18n.json").read_text(encoding="utf-8"))


def _without_comments(text: str) -> str:
    return re.sub(r"/\*.*?\*/", "", text, flags=re.S)


# ── it is a light switch, not a way in ──


def test_the_panel_holds_no_list_of_allowed_capabilities() -> None:
    """A second copy of that rule is a second copy that can drift.

    What a panel may operate is decided by the server from the token it holds.
    If this file named capabilities, the two would eventually disagree and the
    one on the wall would be the one nobody tested.
    """
    code = _without_comments(JS)
    for capability in ("lock.state", "garage.state", "camera.recording", "valve.state"):
        assert capability not in code, capability


def test_a_control_the_panel_cannot_use_is_absent_rather_than_disabled() -> None:
    """A greyed-out lock still tells whoever is standing in the hallway that a
    lock exists and that this screen is the way to it."""
    assert "disabled state here on purpose" in CSS
    # Nothing renders a control from a capability the server did not send.
    assert "device.capabilities" in JS


def test_a_refusal_is_shown_rather_than_swallowed() -> None:
    """The panel must not snap back to the old state as though nothing was
    pressed — somebody standing there needs to know it did not work."""
    code = _without_comments(JS)
    assert "not_allowed_here" in code
    assert "403" in code


# ── it is read from across a room ──


def test_touch_targets_are_bigger_than_a_phone_s() -> None:
    """44px is for a phone held in your hand with your eyes on it. Somebody
    passing a hallway gets one attempt with a thumb, and the whole tile is the
    target rather than a control inside it."""
    match = re.search(r"\.control\s*\{[^}]*min-block-size:\s*(\d+)px", CSS, re.S)
    assert match, "the control has no minimum height"
    assert int(match.group(1)) >= 120, match.group(1)


def test_the_on_state_is_not_carried_by_colour_alone() -> None:
    """§8. A filled tile reads from further away than a coloured border, and
    the label changes with it — so the state survives a glance, a colour-blind
    reader, and a screen with sun on it."""
    assert 'data-on="true"' in CSS
    assert 't("on")' in JS and 't("off")' in JS


def test_a_press_is_acknowledged_because_a_wall_has_no_hover() -> None:
    assert ".control:active" in CSS
    active = CSS[CSS.index(".control:active") :]
    assert "transform" in active[: active.index("}")]


def test_motion_is_fast_and_only_on_press() -> None:
    """A tile that eases for 300ms feels like a delay, and a wall panel is
    competing with a physical switch."""
    control = CSS[CSS.index(".control {") : CSS.index(".control:active")]
    assert "--motion-fast" in control
    assert "animation" not in control


def test_reduced_motion_is_honoured() -> None:
    """Somebody who set it on a wall panel meant it."""
    assert "prefers-reduced-motion" in CSS


def test_the_tiles_reflow_without_a_breakpoint_to_maintain() -> None:
    assert "auto-fill" in CSS or "auto-fit" in CSS
    assert "@media (min-width" not in CSS, "a wall panel has one size at a time"


def test_a_single_tile_stays_a_tile() -> None:
    """`auto-fit` collapses the empty tracks and stretches one device across a
    metre of wall. A house with one switchable light should not look like a
    banner."""
    assert "auto-fill" in CSS


def test_the_glyphs_are_text_rather_than_an_imitated_icon_set() -> None:
    """An icon set is a thing to draw, license and maintain. A wall panel needs
    six shapes, and none of them may be somebody else's."""
    assert "const GLYPHS" in JS
    assert ".svg" not in JS
    assert "aria-hidden" in JS, "the label already says what it is"


def test_nothing_on_the_panel_scrolls() -> None:
    """A pull-to-refresh or a rubber-band bounce on a wall is a gesture nobody
    meant to make."""
    assert "overscroll-behavior: none" in CSS
    assert "overflow: hidden" in CSS


def test_the_panel_dims_at_night_rather_than_going_dark() -> None:
    """A dark rectangle is indistinguishable from a broken one, and somebody
    should see at a glance that the house is still being watched."""
    assert 'data-night="true"' in CSS
    assert "opacity" in CSS.split('data-night="true"')[1][:200]


def test_the_hazard_never_dims() -> None:
    night = CSS[CSS.index('.panel-body[data-night="true"] .hazard') :]
    assert "opacity: 1" in night[: night.index("}")]


# ── the hazard takes the screen ──


def test_a_confirmed_hazard_replaces_the_panel() -> None:
    """This screen may be the only thing somebody sees, and a gas alarm beside
    the air-conditioning temperature is a gas alarm nobody notices."""
    assert "position: fixed" in CSS[CSS.index(".hazard {") :][:200]
    assert 'role="alert"' in HTML
    assert 'aria-live="assertive"' in HTML


def test_the_hazard_does_not_flash() -> None:
    """A flashing screen in a dark hallway is harder to read, not easier, and
    somebody walking towards a gas leak needs to read it."""
    hazard = CSS[CSS.index(".hazard {") : CSS.index(".visually-hidden")]
    assert "animation" not in hazard
    assert "blink" not in hazard.lower()


def test_the_hazard_says_what_the_platform_already_did() -> None:
    """A household reading "gas detected" needs to know whether the valve is
    shut without walking to the kitchen to look."""
    assert "hazard_isolated" in JS
    assert "hazard_not_isolated" in JS
    assert "carried_out" in JS


def test_every_hazard_category_has_wording_in_both_languages() -> None:
    from syltra_contracts import RiskCategory

    for category in RiskCategory:
        key = f"hazard_{category.value.lower()}"
        for language in ("en", "ar"):
            assert key in I18N[language], f"{language}: {key}"


# ── it is honest when it cannot see ──


def test_a_panel_that_cannot_reach_the_hub_says_so() -> None:
    """A stale light switch on a wall is worse than a blank one, because
    somebody trusts it."""
    assert "no_hub" in JS
    assert "not_registered" in JS


def test_the_two_dictionaries_cover_the_same_keys() -> None:
    assert set(I18N["en"]) == set(I18N["ar"])


def test_arabic_is_actually_arabic() -> None:
    for key, value in I18N["ar"].items():
        if key in {"dir"}:
            continue
        assert any("؀" <= ch <= "ۿ" for ch in value), key


def test_every_key_the_panel_uses_exists() -> None:
    used = set(re.findall(r't\("([\w_]+)"\)', JS))
    used |= set(re.findall(r"`hazard_\$\{[^}]+\}`", JS)) and set()
    missing = sorted(used - set(I18N["en"]))
    assert not missing, missing


def test_the_panel_shares_the_design_system_rather_than_copying_it() -> None:
    """Same tokens, same fonts, same RTL rules. A second palette on a wall is a
    second palette to keep in step."""
    assert "/design-system/tokens/tokens.css" in HTML
    assert "/design-system/typography/fonts.css" in HTML
    for hard_coded in ("#fff", "#000"):
        # One exception: hazard text is white on the critical red on purpose,
        # because it must not follow a theme a household chose for comfort.
        assert CSS.count(hard_coded) <= 1, hard_coded


@pytest.mark.parametrize("language", ["en", "ar"])
def test_the_direction_is_declared(language: str) -> None:
    assert I18N[language]["dir"] in ("ltr", "rtl")
