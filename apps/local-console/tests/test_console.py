"""Local console tests (spec §28, ADR-007, Phase 7 acceptance).

Two acceptance criteria live here: **the UI works in Arabic RTL and English
LTR**, and **accessibility checks pass**. The console is static files, so the
tests inspect the actual HTML, CSS, JS and translation dictionary rather than a
rendered DOM — which is enough to catch the failures that matter: a missing
translation, a physical CSS property that will not mirror, an unlabelled
control, or an injection hazard.
"""

import json
import pathlib
import re

import pytest

CONSOLE = pathlib.Path(__file__).resolve().parents[1] / "static"
HTML = (CONSOLE / "index.html").read_text(encoding="utf-8")
# The console has no stylesheet of its own: it is composed entirely from the
# design system. `CSS` is therefore the authored design-system CSS the console
# loads — which is where the rules these tests are about now live.
DESIGN_SYSTEM = CONSOLE.parent / "src" / "design-system"
CSS = "\n".join(
    (DESIGN_SYSTEM / name).read_text(encoding="utf-8")
    for name in ("foundation.css", "primitives.css", "shell.css", "domain.css")
)
JS = (CONSOLE / "console.js").read_text(encoding="utf-8")
I18N = json.loads((CONSOLE / "i18n.json").read_text(encoding="utf-8"))


def _without_comments(source: str) -> str:
    """Strip comments before asserting a construct is absent.

    The console's comments deliberately *name* the things the code avoids —
    "textContent, never innerHTML". Searching raw source would then flag the
    explanation as the offence, so these checks read code only.
    """
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.S)
    return re.sub(r"^\s*//.*$", "", source, flags=re.M)


CSS_CODE = _without_comments(CSS)
JS_CODE = _without_comments(JS)
HTML_CODE = re.sub(r"<!--.*?-->", "", HTML, flags=re.S)


# `syltra.token`, `syltra.locale` and friends are localStorage keys, a
# different namespace that happens to share the dotted shape.
STORAGE_NAMESPACE = "syltra."


def _capabilities_named_in(source: str) -> set[str]:
    return {
        name
        for name in re.findall(r'"([a-z_]+\.[a-z_]+)"', source)
        if not name.startswith(STORAGE_NAMESPACE)
    }


def _call_arguments(source: str, name: str) -> list[str]:
    """Every argument list passed to `name(...)`, matched on balanced parens.

    A regex cannot do this: `badge(x ? t("a") : t("b"), label)` contains parens
    inside its own arguments, and `[^)]*` stops at the first one — quietly
    matching half a call and asserting against the wrong text.
    """
    calls = []
    for match in re.finditer(rf"(?<![\w.]){re.escape(name)}\(", source):
        depth, index = 0, match.end() - 1
        while index < len(source):
            if source[index] == "(":
                depth += 1
            elif source[index] == ")":
                depth -= 1
                if depth == 0:
                    calls.append(source[match.end() : index])
                    break
            index += 1
    return calls


# ── bilingual support ──


def test_both_locales_are_present() -> None:
    assert set(I18N) == {"en", "ar"}


def test_the_two_dictionaries_cover_the_same_keys() -> None:
    # A key present in one language and missing in the other shows the raw key
    # to half the users.
    english, arabic = set(I18N["en"]), set(I18N["ar"])
    assert english == arabic, f"asymmetric keys: {english ^ arabic}"


def test_arabic_declares_rtl_and_english_declares_ltr() -> None:
    assert I18N["ar"]["dir"] == "rtl"
    assert I18N["en"]["dir"] == "ltr"


# `dir` is a direction token, not prose. The product names are the same string
# in every language by §5.4, which says to use "SYLTRA" and "SILA" exactly —
# transliterating a brand name would be a bug, not a translation.
NOT_TRANSLATABLE = {"dir", "actor_platform"}


def test_arabic_strings_are_actually_arabic() -> None:
    # Guards against an entry that quietly copies the English.
    for key, value in I18N["ar"].items():
        if key in NOT_TRANSLATABLE:
            continue
        assert any("؀" <= ch <= "ۿ" for ch in value), f"{key} is not Arabic"


def test_arabic_and_english_text_differ() -> None:
    for key in I18N["en"]:
        if key in NOT_TRANSLATABLE:
            continue
        assert I18N["ar"][key] != I18N["en"][key], f"{key} is identical in both languages"


def test_the_untranslatable_entries_really_are_product_names() -> None:
    # An exemption list is a place bugs hide. Each entry must be a brand name
    # §5.4 fixes, not an English string someone gave up on.
    for key in NOT_TRANSLATABLE - {"dir"}:
        assert I18N["en"][key] in {"SYLTRA", "SILA"}, key


def test_every_translation_key_used_in_the_ui_exists() -> None:
    used = set(re.findall(r'data-i18n="([\w_]+)"', HTML))
    used |= set(re.findall(r't\("([\w_]+)"\)', JS))
    # Table headings reach `t()` through `scrollableTable`, not directly. A
    # heading that is not a key renders as the key itself — which is how a
    # column header reading `state` shipped in the first UI-2 build.
    for headings in re.findall(r"scrollableTable\(\s*\[([^\]]*)\]", JS_CODE, re.S):
        used |= set(re.findall(r'"([a-z_]+)"', headings))
    # Filter labels and option text go through `t()` inside helpers too.
    used |= set(re.findall(r'selectFilter\("[\w-]+", t\("([\w_]+)"\)', JS_CODE))
    known = set(I18N["en"]) | {"skip"}
    missing = used - known
    assert missing == set(), f"UI references untranslated keys: {sorted(missing)}"


def test_the_document_direction_is_set_from_the_locale() -> None:
    assert "document.documentElement.dir = dir" in JS
    assert "document.documentElement.lang = state.locale" in JS


# ── true RTL, not a themed subset ──


@pytest.mark.parametrize(
    "physical",
    [
        "margin-left",
        "margin-right",
        "padding-left",
        "padding-right",
        "border-left",
        "border-right",
        "left:",
        "right:",
        "text-align: left",
        "text-align: right",
    ],
)
def test_no_physical_direction_properties_are_used(physical: str) -> None:
    # Logical properties mirror automatically under dir="rtl"; physical ones do
    # not, and produce a layout that is half-mirrored.
    assert physical not in CSS_CODE, f"{physical} will not mirror in Arabic"


def test_logical_properties_are_used_for_direction_sensitive_styling() -> None:
    for logical in (
        "margin-inline-start",
        "padding-inline-start",
        "border-inline-start",
        "inset-inline-start",
        "text-align: start",
    ):
        assert logical in CSS, f"expected {logical} for RTL-safe layout"


def test_the_sidebar_is_navigable_by_keyboard() -> None:
    # UI-1 acceptance: keyboard navigation passes. The sidebar is a vertical
    # list, so Up and Down move through it and Home and End jump to the ends.
    #
    # The horizontal tab strip this replaced needed direction-aware arrow keys,
    # because ArrowRight means "previous" in Arabic. Vertical order is identical
    # in both languages, so that logic is gone rather than merely untested.
    for key in ('"ArrowDown"', '"ArrowUp"', '"Home"', '"End"'):
        assert key in JS_CODE, key
    assert "next.focus()" in JS_CODE


def test_focus_moves_through_the_sidebar_without_navigating() -> None:
    # An arrow key that also changed the view would make every item below the
    # first unreachable by keyboard: you would land on it and immediately be
    # taken elsewhere. Only focus moves; Enter and Space activate, as they
    # already do for a link.
    handler = re.search(r"function bindNavKeys\(.*?\n\}", JS_CODE, re.S)
    assert handler
    assert "route(" not in handler.group(0)
    assert "click(" not in handler.group(0)


# ── accessibility ──


def test_the_page_declares_a_language_and_direction() -> None:
    assert re.search(r'<html lang="en" dir="ltr">', HTML)


def test_there_is_a_skip_link_to_the_main_content() -> None:
    assert 'class="skip-link" href="#main"' in HTML
    assert 'id="main"' in HTML


def test_the_shell_uses_one_persistent_labelled_sidebar() -> None:
    # §4: one persistent desktop sidebar, never two competing ones.
    assert HTML_CODE.count('class="app-sidebar"') == 1
    assert HTML_CODE.count('class="app-nav"') == 1
    assert HTML_CODE.count("<nav") == 1
    # The landmark carries a name, and the name is translated.
    assert 'data-i18n-aria-label="nav_label"' in HTML_CODE
    assert "nav_label" in I18N["en"] and "nav_label" in I18N["ar"]


def test_the_shell_exists_before_any_data_arrives() -> None:
    # A failed API call should leave an empty shell with an error, not a blank
    # page — so the sidebar, top bar and content region are markup, not script.
    for part in ("app-shell", "app-sidebar", "app-topbar", "app-content"):
        assert part in HTML_CODE, part


def test_navigation_covers_the_specified_information_architecture() -> None:
    # §4 fixes the primary navigation and its order. An item missing here is an
    # item a user cannot reach; an extra one is an invented product surface.
    expected = [
        "overview",
        "properties",
        "rooms",
        "devices",
        "automations",
        "intelligence",
        "risks",
        "energy",
        "installations",
        "users",
        "audit",
        "health",
        "settings",
    ]
    found = re.findall(r'\{ id: "([a-z]+)"', JS_CODE)
    assert found == expected, found


def test_every_navigation_item_is_named_in_both_languages() -> None:
    for item in re.findall(r'\{ id: "([a-z]+)"', JS_CODE):
        key = f"nav_{item}"
        assert key in I18N["en"], key
        assert key in I18N["ar"], key


def test_the_language_selector_is_labelled() -> None:
    # A bare <select> is unusable with a screen reader.
    assert 'for="locale"' in HTML
    assert 'id="locale"' in HTML
    assert "aria-describedby" in HTML


def test_status_updates_are_announced_politely() -> None:
    assert 'role="status"' in HTML
    assert 'aria-live="polite"' in HTML


def test_focus_is_always_visible() -> None:
    assert ":focus-visible" in CSS
    assert "outline: var(--control-focus-ring-width) solid var(--focus-ring)" in CSS


def test_the_current_view_is_exposed_to_assistive_technology() -> None:
    # `aria-current="page"` is the sidebar equivalent of aria-selected, and the
    # stylesheet pairs it with an edge bar so the state is not colour alone.
    assert 'setAttribute("aria-current", "page")' in JS_CODE
    assert 'removeAttribute("aria-current")' in JS_CODE


def test_the_viewport_allows_zooming() -> None:
    # No `maximum-scale` or `user-scalable=no`, which would block magnification.
    assert "maximum-scale" not in HTML
    assert "user-scalable" not in HTML


def test_the_layout_is_responsive() -> None:
    assert "@media (max-width" in CSS
    assert "minmax(" in CSS


def test_colour_is_not_the_only_status_signal() -> None:
    # Risk and context cards carry a text badge as well as a coloured border.
    # The badge is the design system's, which gives advisory, confirmed and
    # shadow three distinct border styles — checked in
    # `test_design_system.py::test_advisory_confirmed_and_shadow_differ_by_more_than_colour`.
    # This test asserts the console reaches for it, everywhere a state is shown.
    calls = [c for c in _call_arguments(JS_CODE, "badge") if not c.startswith("variant")]
    variants = {v for call in calls for v in re.findall(r'"([a-z]+)"', call.split(",")[0])}
    assert {"advisory", "confirmed", "shadow"} <= variants, variants
    # Every badge carries a label as well as a variant, so the state is legible
    # without seeing the colour at all.
    for call in calls:
        assert "," in call, call


# ── safety and privacy in the UI ──


@pytest.mark.safety
def test_the_console_never_writes_untrusted_values_as_markup() -> None:
    # Everything from the API goes through textContent. A device a household
    # named "<img onerror=...>" must render as text, not as an element.
    assert "innerHTML" not in JS_CODE
    assert "insertAdjacentHTML" not in JS_CODE
    assert "document.write" not in JS_CODE
    assert "eval(" not in JS_CODE
    # And the safe alternative is actually used.
    assert "textContent" in JS_CODE


@pytest.mark.safety
def test_advisory_risk_cases_are_labelled_as_advisory() -> None:
    # A household must never be shown a watch as a confirmed emergency.
    assert 'badge(item.advisory ? "advisory" : "confirmed"' in JS_CODE
    assert 't(item.advisory ? "advisory" : "confirmed")' in JS_CODE
    # A confirmed case additionally says *what* confirmed it, so a reader can
    # tell a certified detector from a model without knowing the architecture.
    assert "confirmed_explanation" in JS_CODE
    assert "advisory_explanation" in JS_CODE
    assert I18N["en"]["advisory"] == "Advisory — not confirmed"
    assert "غير مؤكد" in I18N["ar"]["advisory"]


@pytest.mark.safety
def test_shadow_recommendations_cannot_be_acted_on() -> None:
    # Spec §19.2: shadow predictions are not shown as actionable. The console
    # used to render a disabled button; it now renders no control at all, which
    # is strictly stronger — there is nothing to re-enable from a devtools
    # console.
    #
    # Asserted structurally rather than by matching one line: the only place
    # that builds a decision control must sit behind a guard that excludes
    # shadow items.
    creations = re.findall(r"(?<!function )decisionButton\(", JS_CODE)
    assert len(creations) == 2, f"approve and reject, built in one place: {creations}"
    before = JS_CODE[: JS_CODE.index("decisionButton(item")]
    guard = before.rsplit("if (", 1)[1]
    # The guard is now a named condition. Follow it to its definition rather
    # than requiring the literal, so the test tracks the meaning: a decision
    # control appears only for a non-shadow proposal that policy has actually
    # put to a person.
    assert "awaiting" in guard
    awaiting = re.search(r"const awaiting =(.*?);", JS_CODE, re.S)
    assert awaiting
    assert "!item.shadow" in awaiting.group(1)
    assert "REQUIRE_USER_APPROVAL" in awaiting.group(1)


@pytest.mark.safety
def test_the_console_never_reaches_a_safety_capability() -> None:
    # Spec §0 and invariant 18: life-safety actuators are commanded by the
    # Safety Governor, never by a person in a UI. The console must not name one.
    for forbidden in ("ACT_SAFETY", "safety.valve", "safety.breaker", "safety.siren"):
        assert forbidden not in JS_CODE, forbidden


@pytest.mark.safety
def test_the_console_shows_no_credentials_or_broker_details() -> None:
    # Spec §28: the console must not expose raw tokens or broker credentials.
    for forbidden in ("nats://", "postgresql://", "NATS_PASSWORD", "POSTGRES_PASSWORD"):
        assert forbidden not in JS_CODE
        assert forbidden not in HTML_CODE


@pytest.mark.safety
def test_the_console_offers_no_unrestricted_actuator_control() -> None:
    # Spec §28: no unrestricted actuator commands. The console's only mutations
    # are approve, reject and feedback — all of which go through policy.
    mutations = set(re.findall(r'method: "(\w+)"', JS_CODE))
    assert mutations <= {"POST"}
    endpoints = set(re.findall(r'api\(`?([^`",]+)', JS_CODE))
    assert not any("actions/manual" in e for e in endpoints)


def test_reason_codes_are_rendered_from_the_api_not_translated_locally() -> None:
    # The API already translated them; translating again in the console would
    # let the two disagree.
    assert "item.reasons" in JS or "context.reasons" in JS
    assert "REASON_CODES" not in JS_CODE


def test_privacy_panel_states_the_local_first_position() -> None:
    assert "stays on this hub" in I18N["en"]["privacy_note"]
    assert "بيانات منزلك تبقى" in I18N["ar"]["privacy_note"]


# ── no external dependencies (ADR-007) ──


def test_nothing_is_fetched_from_the_internet() -> None:
    # The hub may have no internet (spec §4.2), and a console that degrades
    # without it is not a local-first console.
    for asset in (HTML_CODE, CSS_CODE, JS_CODE):
        assert "http://" not in asset
        assert "https://" not in asset
        assert "cdn." not in asset
        assert "@import url(" not in asset


def test_no_build_step_is_implied() -> None:
    assert not (CONSOLE.parent / "package.json").exists()
    assert not (CONSOLE.parent / "node_modules").exists()


def test_no_font_is_fetched_over_the_network() -> None:
    # The hub may have no internet (spec §4.2), so a font the console cannot
    # reach must degrade to one the operating system already has. Typography
    # moved to the design system in UI-0, so the stack is checked there — what
    # stays true of both is that nothing is fetched and a system fallback ends
    # every list.
    typography = (
        CONSOLE.parent / "src" / "design-system" / "typography" / "typography.css"
    ).read_text(encoding="utf-8")
    for stylesheet in (CSS, typography):
        assert "@font-face" not in stylesheet
        assert "@import" not in stylesheet
    for family in re.findall(r"--font-\w+:\s*([^;]+);", typography):
        assert re.search(r"(system-ui|sans-serif|monospace)\s*$", family.strip()), family


def test_the_console_carries_no_palette_of_its_own() -> None:
    # UI-0 acceptance: no feature component contains a hardcoded brand colour.
    # The console is a feature component, so every colour it paints must arrive
    # through a design-system token.
    assert not re.findall(r"#[0-9a-fA-F]{3,8}\b", CSS)
    assert "prefers-color-scheme" not in CSS_CODE, "theming belongs to the theme files"


def test_the_console_is_composed_entirely_from_the_design_system() -> None:
    # The console has no stylesheet of its own. That is what makes "no feature
    # component contains a hardcoded brand colour" true by construction rather
    # than by review: there is no file left for one to hide in.
    links = re.findall(r'<link rel="stylesheet" href="([^"]+)"', HTML)
    assert links, "the console loads no stylesheet at all"
    assert all(link.startswith("/design-system/") for link in links), links
    assert not (CONSOLE / "console.css").exists()
    # Dark is declared before light, so an explicit light choice wins.
    assert links.index("/design-system/themes/dark-theme.css") < links.index(
        "/design-system/themes/light-theme.css"
    )


# ── navigation filtering (§3, §4) ──


def test_navigation_is_filtered_by_permission_not_by_role_name() -> None:
    # The guidelines describe six personas; the platform issues six roles whose
    # names do not match them. Filtering on permissions rather than role names
    # means the console follows the authority the backend actually grants, and
    # keeps working when a role's permission set changes.
    assert 'permission: "' in JS_CODE
    assert "visibleNav" in JS_CODE
    assert "NAV.filter((item) => may(item.permission))" in JS_CODE
    assert "role ===" not in JS_CODE, "no navigation decision may turn on a role name"


def test_the_sensitive_sections_name_the_permission_they_need() -> None:
    # Audit reveals who did what, and is not implied by seeing the home.
    entries = dict(re.findall(r'\{ id: "([a-z]+)", icon: "[^"]+", permission: "(\w+)"', JS_CODE))
    assert entries["audit"] == "READ_AUDIT"
    # Users is READ_HOME on purpose: knowing who else holds a key to the house
    # you live in is not a privileged question. Changing anything on that
    # screen needs MANAGE_USERS, which the API enforces and the screen reflects
    # by rendering no controls without it.
    assert entries["users"] == "READ_HOME"
    assert "may_manage" in JS_CODE, "the screen must gate its controls on the server's answer"
    # Everything else is readable by anyone who can see the home.
    assert entries["overview"] == "READ_HOME"


def test_hiding_is_documented_as_presentation_only() -> None:
    # §3: "Hidden access is not authorization." The claim is enforced in
    # `services/api-gateway/tests/test_identity.py`; this checks the console
    # says so where the next person will read it, rather than leaving the
    # filter looking like a security control.
    assert "not authorization" in JS.lower() or "is not authorization" in JS.lower()


def test_a_stale_property_preference_falls_back_instead_of_failing() -> None:
    # A remembered home the token no longer covers is a stale preference, not
    # an error. Requesting it anyway would produce a wall of 403s on a screen
    # the user cannot fix from.
    assert "homes.includes(requested) ? requested : homes[0]" in JS_CODE


def test_privacy_actions_are_gated_on_the_privacy_permission() -> None:
    assert 'may("MANAGE_PRIVACY")' in JS_CODE
    assert 'may("APPROVE_RECOMMENDATION")' in JS_CODE


def test_unavailable_sections_are_marked_rather_than_hidden() -> None:
    # §20: an absent capability is a designed state. Silently dropping half the
    # information architecture would make the console look finished.
    unavailable = re.findall(r'\{ id: "([a-z]+)"[^}]*unavailable: true', JS_CODE)
    # Properties became real in UI-2 (the caller's own scope), Energy in UI-4,
    # Automations once the engine existed, and Users once the directory did.
    # What is left is what the platform genuinely does not produce: there is no
    # installation project.
    assert set(unavailable) == {"installations"}, unavailable
    assert "not_yet_available" in JS_CODE
    assert "not_yet_available" in I18N["en"] and "not_yet_available" in I18N["ar"]


# ── §17.7 role-based device detail ──


def test_low_level_identifiers_are_gated_on_the_diagnostics_permission() -> None:
    # §17.7: "hide low-level identifiers from ordinary users and expose them to
    # authorized technicians". Verified live across all five roles: OWNER and
    # INSTALLER see `climate.target_temperature`; ADULT, CHILD and GUEST see
    # "target temperature" and no diagnostics block at all.
    assert 'may("READ_DIAGNOSTICS")' in JS_CODE
    # The capability list switches label, not just visibility — a raw entity id
    # sitting in a table is the leak, whether or not a panel below it is shown.
    assert "friendlyCapability" in JS_CODE
    # The diagnostics panel is built in exactly one place, behind the check.
    start = JS_CODE.index('el("div", "diagnostics")')
    guard = JS_CODE[:start].rsplit("if (", 1)[1]
    assert 'may("READ_DIAGNOSTICS")' in guard, guard[:80]
    panel = JS_CODE[start : JS_CODE.index("host.append(diagnostics)")]
    assert "device_id" in panel and "identifier" in panel


def test_the_diagnostics_permission_is_not_implied_by_reading_the_home() -> None:
    # A household member seeing the living-room temperature has no reason to
    # see the integration's entity id. The permission exists precisely so the
    # console does not have to test for a role name.
    from syltra_security import ROLE_PERMISSIONS, Permission, Role

    assert Permission.READ_DIAGNOSTICS in ROLE_PERMISSIONS[Role.OWNER]
    assert Permission.READ_DIAGNOSTICS in ROLE_PERMISSIONS[Role.INSTALLER]
    for role in (Role.ADULT, Role.CHILD, Role.GUEST, Role.SERVICE):
        assert Permission.READ_HOME in ROLE_PERMISSIONS[role]
        assert Permission.READ_DIAGNOSTICS not in ROLE_PERMISSIONS[role], role


# ── §20 data states ──


def test_every_state_section_twenty_requires_is_implemented() -> None:
    # §20 lists eleven states. Each needs a distinct thing to say; a shared
    # "something went wrong" would defeat the point of listing them.
    variants = {
        v
        for call in _call_arguments(JS_CODE, "notice")
        for v in re.findall(r'"(partial|offline|stale|denied|failure)"', call.split(",")[0])
    }
    assert {"partial", "offline", "stale", "denied", "failure"} <= variants, variants
    for key in (
        "partial_title",
        "denied_title",
        "failure_title",
        "no_matches",
        "detail_stale_title",
        "detail_offline_title",
    ):
        assert key in I18N["en"] and key in I18N["ar"], key


def test_no_state_message_is_something_went_wrong() -> None:
    # §20: "Never replace a detailed failure with 'Something went wrong'."
    for locale in ("en", "ar"):
        for value in I18N[locale].values():
            assert "something went wrong" not in value.lower()
    assert "حدث خطأ ما" not in " ".join(I18N["ar"].values())


def test_a_partial_load_names_what_is_missing() -> None:
    # "Some data could not be loaded" without saying which is the same as
    # saying nothing.
    assert "{what}" in I18N["en"]["partial_detail"]
    assert "{what}" in I18N["ar"]["partial_detail"]
    assert "loadAll" in JS_CODE
    assert "Promise.allSettled" in JS_CODE, "Promise.all would discard the data that loaded"


def test_an_empty_filtered_result_is_not_an_empty_home() -> None:
    # §20 lists these as different states because they need different words.
    assert "no_matches" in JS_CODE
    assert "no_devices" in JS_CODE
    assert I18N["en"]["no_matches"] != I18N["en"]["no_devices"]


def test_device_state_comes_from_the_platforms_freshness_rule() -> None:
    # The Digital Twin marks each reading against that capability's own
    # `freshness_seconds`, so a gas detector and a power meter are judged by
    # their own standards. A threshold invented in the console would override
    # that with one number for everything.
    assert '"STALE"' in JS_CODE and '"KNOWN"' in JS_CODE and '"UNKNOWN"' in JS_CODE
    assert not re.search(r"age_seconds\s*[<>]=?\s*\d", JS_CODE), "no invented staleness threshold"


@pytest.mark.safety
def test_a_stale_or_offline_device_never_reads_as_normal() -> None:
    # §20: "Do not show a safe or normal state when data is unavailable." A
    # blank availability cell would read as nothing wrong.
    assert 'state: "stale"' in JS_CODE
    assert 'state: "offline"' in JS_CODE
    assert 'state: "unknown"' in JS_CODE
    # A device reporting only some capabilities is degraded, not online.
    assert 'state: "degraded"' in JS_CODE
    assert "state_unknown_detail" in JS_CODE, "unknown needs an explanation, not a blank"


# ── UI-3 acceptance: intelligence and action screens ──


@pytest.mark.safety
def test_sila_cannot_appear_to_bypass_policy() -> None:
    # The acceptance criterion is about what a person can be led to believe.
    # Every proposal carries the decision policy reached, so a recommendation
    # can never look like something SYLTRA is about to do on its own.
    assert "policyPanel" in JS_CODE
    for outcome in (
        "policy_ALLOW",
        "policy_DENY",
        "policy_REQUIRE_USER_APPROVAL",
        "policy_PREPARE_ONLY",
        "policy_ESCALATE_TO_FIXED_SAFETY_RULE",
    ):
        assert outcome in I18N["en"] and outcome in I18N["ar"], outcome
    # A proposal with no decision is reported as such rather than shown bare.
    assert "policy_missing_title" in JS_CODE


@pytest.mark.safety
def test_an_approval_control_appears_only_where_policy_asked_for_one() -> None:
    # Rendering Approve against a DENY invites a click that cannot succeed and
    # implies the refusal is negotiable. Rendering it for a shadow prediction
    # would be the §19.2 bypass outright.
    awaiting = re.search(r"const awaiting =(.*?);", JS_CODE, re.S)
    assert awaiting
    condition = awaiting.group(1)
    assert "!item.shadow" in condition
    assert "item.policy" in condition
    assert "REQUIRE_USER_APPROVAL" in condition


def test_the_result_reported_is_what_policy_decided_not_what_was_clicked() -> None:
    # An approval that policy turns into something other than ALLOW is the case
    # a person most needs told about.
    handler = JS_CODE[JS_CODE.index("function decisionButton") :]
    handler = handler[: handler.index("\n}")]
    assert "result.decision" in handler
    assert "await refresh()" in handler
    # The confirmation is set after the refresh: refresh clears the status
    # line, so setting it first made the message flash and vanish.
    assert handler.index("await refresh()") < handler.index('setStatus(`${t("policy_decided")}')


def test_all_six_feedback_responses_are_available() -> None:
    # §13.4 lists approve, reject, not now, modify, never repeat — and undo,
    # which belongs to an action that has run rather than to a proposal.
    kinds = set(re.findall(r'"(ACCEPT|REJECT|NOT_NOW|MODIFY|NEVER_REPEAT|UNDO)"', JS_CODE))
    assert {"NOT_NOW", "MODIFY", "NEVER_REPEAT"} <= kinds
    assert 'decisionButton(item, "approve"' in JS_CODE
    assert 'decisionButton(item, "reject"' in JS_CODE


def test_feedback_is_open_to_anyone_who_can_see_the_home() -> None:
    # A person who may not approve an action can still say it was a bad idea,
    # and the models should hear it. Feedback sits outside the approval gate.
    actions = JS_CODE[JS_CODE.index("function feedbackActions") :]
    actions = actions[: actions.index("\n}")]
    feedback_part = actions[actions.index("for (const kind of FEEDBACK_KINDS)") :]
    assert "APPROVE_RECOMMENDATION" not in feedback_part


@pytest.mark.safety
def test_the_active_learning_mode_and_what_it_permits_are_both_shown() -> None:
    # §16: "The UI must always show the active mode and what the mode permits."
    # A mode name alone tells a household nothing about whether the platform is
    # about to do something.
    assert "learningModeBanner" in JS_CODE
    for mode in (
        "DISABLED",
        "OBSERVE",
        "SHADOW",
        "RECOMMEND",
        "APPROVAL_REQUIRED",
        "AUTHORIZED_AUTOMATION",
        "SUSPENDED",
    ):
        assert f"mode_{mode}" in I18N["en"], mode
        assert f"mode_{mode}_permits" in I18N["en"], mode
        assert f"mode_{mode}_permits" in I18N["ar"], mode


@pytest.mark.safety
def test_manual_override_is_visible_in_the_timeline() -> None:
    # The platform rule is that manual control always wins. A timeline that
    # listed an override as one more automated step would hide the fact that
    # a person took over.
    assert "MANUAL_OVERRIDE_DETECTED" in JS_CODE
    assert "ACTION_CANCELLED_BY_MANUAL_OVERRIDE" in JS_CODE
    assert "OVERRIDE_STAGES" in JS_CODE
    assert I18N["en"]["stage_override"] and I18N["ar"]["stage_override"]


def test_the_timeline_reads_forwards() -> None:
    # §13.7's stages have a natural sequence. The audit feed arrives newest
    # first, which is right for a log and inverts cause and effect in a
    # timeline.
    body = JS_CODE[JS_CODE.index("function timeline(") :]
    body = body[: body.index("\n}")]
    assert "new Date(a.occurred_at) - new Date(b.occurred_at)" in body


def test_correlation_ids_are_for_technicians_only() -> None:
    # §13.7: "correlation ID access for authorized technicians".
    body = JS_CODE[JS_CODE.index("function timeline(") :]
    body = body[: body.index("\n}")]
    assert 'may("READ_DIAGNOSTICS")' in body
    assert "correlation_id" in body


def test_the_risk_centre_puts_confirmed_hazards_first() -> None:
    # §17.10 fixes the order, and the order is the safety argument: a confirmed
    # hazard is never below an advisory watch, however recent the watch is.
    order = re.search(r"const RISK_STATE_ORDER = \[(.*?)\]", JS_CODE, re.S)
    assert order
    states = re.findall(r'"(\w+)"', order.group(1))
    assert states[0] == "CONFIRMED"
    assert states.index("PRE_ALERT") < states.index("WATCH")
    assert states.index("WATCH") < states.index("RECOVERY")


def test_model_internals_are_not_shown_to_household_users() -> None:
    # §17.9: "Do not display raw model internals to household users. Provide
    # deeper technical view to authorized administrators."
    assert "models_technical_label" in JS_CODE
    guard = JS_CODE[: JS_CODE.index("models_technical_label")].rsplit("if (", 1)[1]
    assert 'may("MANAGE_MODELS")' in guard or 'may("READ_DIAGNOSTICS")' in guard
    # A household user still learns where a proposal came from, in plain words.
    assert "from_learned_pattern" in JS_CODE


# ── the console names real capabilities, with the meanings the contract gives ──


def test_every_capability_the_console_names_exists() -> None:
    # `light.on` was read for the lights-on count. It is not a capability the
    # platform defines, so the count was always zero and every room card
    # quietly claimed the lights were off. Nothing failed; the number was just
    # wrong.
    from syltra_contracts.capability_definitions import ALL_CAPABILITIES

    named = _capabilities_named_in(JS_CODE)
    unknown = sorted(named - set(ALL_CAPABILITIES))
    assert not unknown, f"the console reads capabilities the platform does not define: {unknown}"


def test_the_console_does_not_infer_meaning_from_a_capability_name() -> None:
    # `light.power` and `switch.power` are boolean on/off controls. Matching on
    # the word "power" summed `true` into a wattage total and reported the home
    # as twice as well metered as it is — §17.11 forbids exactly that kind of
    # device-level estimate, and an inflated coverage figure makes an
    # incomplete number look complete.
    assert 'const POWER_UNIT = "W"' in JS_CODE
    assert "reading.unit === POWER_UNIT" in JS_CODE
    assert "POWER_CAPABILITIES" not in JS_CODE


def test_boolean_capabilities_are_never_treated_as_quantities() -> None:
    from syltra_contracts.capability_definitions import (
        ALL_CAPABILITIES,
        DataType,
        get_definition,
    )

    booleans = {
        capability
        for capability in ALL_CAPABILITIES
        if get_definition(capability).data_type is DataType.BOOLEAN
    }
    # Every boolean the console names must be read as a state, never summed.
    for capability in booleans & _capabilities_named_in(JS_CODE):
        uses = [line for line in JS_CODE.splitlines() if f'"{capability}"' in line]
        for line in uses:
            assert "sum" not in line.lower(), f"{capability} is boolean: {line.strip()}"


@pytest.mark.safety
def test_the_energy_screen_states_what_it_cannot_measure() -> None:
    # §17.11: "Never fabricate cost, savings, carbon, or device-level
    # estimates." There is no time-series endpoint, so consumption over time,
    # baseline comparison and cost are all absent — and named as absent, rather
    # than left as a gap a reader fills in themselves.
    assert "energy_not_measured" in JS_CODE
    detail = I18N["en"]["energy_not_measured_detail"].lower()
    for missing in ("trend", "cost"):
        assert missing in detail, missing
    # And none of the forbidden quantities is computed anywhere.
    for forbidden in ("carbon", "co2", "tariff", "savings"):
        assert forbidden not in JS_CODE.lower(), forbidden


def test_data_completeness_is_shown_before_the_numbers_it_qualifies() -> None:
    # A total from two of nine meters is a different claim from the same total
    # from all nine. Putting coverage after the number invites reading the
    # number first and the caveat never.
    body = JS_CODE[JS_CODE.index("async function renderEnergy") :]
    body = body[: body.index("\nfunction dataQuality")]
    assert body.index("dataQuality(") < body.index("current_power")


def test_the_coverage_bar_carries_an_accessible_label() -> None:
    # §18: a bar that only exists visually tells a screen reader nothing, and
    # this one restates a number rather than carrying one of its own.
    assert 'bar.setAttribute("role", "img")' in JS_CODE
    assert "coverage_label" in JS_CODE
    assert "{n}" in I18N["en"]["coverage_label"]


def test_a_bad_link_is_reported_as_a_bad_link_not_a_service_failure() -> None:
    # `/v1/homes/{id}/risks/{case_id}` returns 404 for an unknown case and 422
    # for an id that is not a UUID at all. Both are a bad address; reporting
    # either as "risk cases could not be loaded" blames the service for a
    # mistyped URL, which §20 explicitly rules out.
    body = JS_CODE[JS_CODE.index("async function renderRiskDetail") :]
    body = body[: body.index("\n}")]
    assert "error.status === 404" in body
    assert "error.status === 422" in body
    assert "risk_not_found" in body


# ── UI-5 acceptance: audit and settings ──


@pytest.mark.safety
def test_the_audit_trail_offers_no_way_to_change_it() -> None:
    # §17.14: "Audit history is append-only in UI. Do not present edit or
    # delete actions." An audit trail a console can edit is not an audit trail,
    # so this is structural: the renderer builds no control that could mutate
    # an entry, and no request other than the read.
    body = JS_CODE[JS_CODE.index("async function renderAudit") :]
    body = body[: body.index("async function renderHealth")]
    assert "method:" not in body, "the audit view issues no write"
    for verb in ("DELETE", "PATCH", "PUT"):
        assert verb not in body, verb
    # The only element it creates that a person can press is a filter.
    buttons = re.findall(r'el\("button"', body)
    assert not buttons, "the audit view renders no buttons at all"
    assert "audit_readonly_title" in body


def test_the_audit_view_shows_the_fields_the_platform_records() -> None:
    # §17.14 lists ten. Eight are recorded; the screen shows those and names
    # the two that are not, rather than leaving blank columns.
    body = JS_CODE[JS_CODE.index("async function renderAudit") :]
    body = body[: body.index("async function renderHealth")]
    for column in ("when", "event_category", "what", "target", "who", "why", "result"):
        assert f'"{column}"' in body, column
    assert "audit_fields_missing" in body
    detail = I18N["en"]["audit_fields_missing_detail"].lower()
    assert "role" in detail and "correlation" in detail


def test_an_action_audit_entry_can_say_what_it_acted_on() -> None:
    # The API used to drop the orchestrator's `detail`, so the trail could say
    # something was dispatched but not to what — the first thing an incident
    # review needs, and a §17.14 field.
    assert "auditTarget" in JS_CODE
    assert "entry.device_id" in JS_CODE
    assert "entry.capability" in JS_CODE


def test_the_density_modes_the_tokens_carry_are_actually_selectable() -> None:
    # §8.4 requires Comfortable and Compact. The tokens have carried both since
    # UI-0; nothing offered the choice, and a density mode no one can select is
    # a density mode the product does not have.
    assert "applyDensity" in JS_CODE
    assert '"comfortable"' in JS_CODE and '"compact"' in JS_CODE
    assert "syltra.density" in JS_CODE
    # Applied at boot, not only while the settings screen is open.
    boot = JS_CODE[JS_CODE.index("async function boot()") :]
    assert "applyDensity(currentDensity())" in boot


@pytest.mark.safety
def test_privacy_export_and_deletion_are_not_one_click() -> None:
    # §21 rules out one-click destructive actions, and a household's entire
    # record is the most destructive thing here. The controls are present so
    # the capability is discoverable, and disabled so it is not a single press.
    body = JS_CODE[JS_CODE.index("function renderSettings") :]
    body = body[: body.index("\nfunction settingRow")]
    assert "button.disabled = true" in body
    assert "privacy_via_operator" in body
    assert "method:" not in body, "settings issues no write of its own"


def test_settings_does_not_pretend_to_manage_users() -> None:
    # A permissions editor that cannot save is worse than none: it implies the
    # change took effect.
    assert "platform_settings_missing" in JS_CODE
    detail = I18N["en"]["platform_settings_missing_detail"].lower()
    assert "would be worse than none" in detail or "worse than none" in detail


# ── UI-6 hardening ──


PRIMARY_RENDERERS = [
    "renderOverview",
    "renderProperties",
    "renderPropertyDetail",
    "renderRooms",
    "renderRoomDetail",
    "renderDevices",
    "renderDeviceDetail",
    "renderIntelligence",
    "renderRisks",
    "renderRiskDetail",
    "renderEnergy",
    "renderAudit",
    "renderHealth",
]


def _renderer_body(name: str) -> str:
    start = JS_CODE.index(f"function {name}(")
    rest = JS_CODE[start:]
    # Up to the next top-level function declaration.
    match = re.search(r"\n(?:async )?function ", rest[1:])
    return rest[: match.start() + 1] if match else rest


# A renderer may delegate a state to a helper — `renderRooms` reports "no
# rooms" through `roomCards`. Following one level keeps the test about the
# screen's behaviour rather than its call graph.
DELEGATES = {
    "renderRooms": ["roomCards"],
    "renderPropertyDetail": ["roomCards", "contextList", "actionTable", "deviceTable"],
    "renderRoomDetail": ["contextList", "deviceTable", "riskList"],
    "renderIntelligence": ["contextList", "recommendationList"],
    "renderHealth": ["actionTable", "timeline"],
}


def _renderer_with_helpers(name: str) -> str:
    body = _renderer_body(name)
    for helper in DELEGATES.get(name, []):
        body += _renderer_body(helper)
    return body


@pytest.mark.parametrize("renderer", PRIMARY_RENDERERS)
def test_every_primary_screen_can_report_a_failure(renderer: str) -> None:
    # §26 UI-6: "loading, empty, error, offline, stale, and permission states
    # exist for every primary screen." Loading is the shared skeleton in
    # `refresh`, and permission-denied and offline are shapes of `failureNotice`
    # — what each renderer must own is the ability to say *this* view failed
    # without taking the whole page down.
    body = _renderer_with_helpers(renderer)
    assert "failureNotice" in body or "notice(" in body, renderer


@pytest.mark.parametrize("renderer", PRIMARY_RENDERERS)
def test_every_primary_screen_can_report_having_nothing_to_show(renderer: str) -> None:
    # An empty screen with no words on it is indistinguishable from a broken
    # one, and §20 asks for the difference to be visible.
    body = _renderer_with_helpers(renderer)
    assert "emptyNotice" in body or "notice(" in body, renderer


def test_loading_and_permission_states_are_shared_rather_than_per_screen() -> None:
    # These two are identical on every screen, so they live in one place: a
    # skeleton before the render and a denied notice derived from the status
    # code. Re-implementing them per screen is how they drift.
    assert "loadingSkeleton" in JS_CODE
    refresh = _renderer_body("refresh")
    assert "loadingSkeleton()" in refresh
    assert 'error.key === "forbidden"' in JS_CODE
    assert "denied_title" in JS_CODE


def test_a_partial_failure_does_not_discard_the_data_that_loaded() -> None:
    # §20: "Preserve unaffected data." Every multi-source screen uses the
    # settling loader rather than Promise.all.
    for renderer in (
        "renderOverview",
        "renderPropertyDetail",
        "renderEnergy",
        "renderIntelligence",
    ):
        body = _renderer_body(renderer)
        assert "loadHomeView" in body, renderer
        assert "Promise.all(" not in body, renderer


# ── localization review ──


def test_no_user_facing_english_is_hardcoded_in_the_script() -> None:
    # Every visible string goes through `t()`. A sentence written straight into
    # the JavaScript is a string the Arabic build cannot reach.
    #
    # Checked at the two places prose can actually enter the DOM: the third
    # argument of `el(tag, class, text)`, and a `textContent` assignment. A
    # blanket scan of string literals cannot tell a sentence from the code
    # between two strings, and reports the gaps as findings.
    literals = []
    for call in _call_arguments(JS_CODE, "el"):
        parts = _split_arguments(call)
        if len(parts) >= 3:
            literals.append(parts[2].strip())
    literals += re.findall(r"\.textContent\s*=\s*([^;]+);", JS_CODE)

    prose = [
        value
        for value in literals
        if value.startswith('"')
        and " " in value
        and not value.strip('"').isupper()
        and value.strip('"') not in {"—", "-"}
    ]
    assert not prose, f"hardcoded English: {prose}"


def test_every_translated_string_is_reachable_from_the_ui() -> None:
    # The mirror of the missing-key test: a key nothing reads is a string
    # nobody maintains, and it rots.
    #
    # Keys reach `t()` three ways — directly, through a helper such as
    # `emptyNotice("no_rooms")`, and through a lookup map whose values are
    # keys. Any string literal that happens to be a key could be any of those,
    # so the scan is deliberately generous: it is looking for keys nothing
    # could possibly reach.
    reachable = set(re.findall(r'data-i18n(?:-aria-label)?="([\w_]+)"', HTML))
    reachable |= set(re.findall(r'"([a-z][\w_]*)"', JS_CODE))
    reachable |= set(re.findall(r"`([a-z][\w_]*)`", JS_CODE))
    # Keys composed at runtime: `t(`state_${name}`)` and friends.
    prefixes = tuple(m + "_" for m in re.findall(r"t\(`(\w+?)_\$\{", JS_CODE))
    # Keys assembled into a variable first: `const key = \`model_${...}\``.
    prefixes += tuple(m + "_" for m in re.findall(r"=\s*`(\w+?)_\$\{", JS_CODE))
    unused = sorted(
        key
        for key in I18N["en"]
        if key not in reachable and not (prefixes and key.startswith(prefixes)) and key != "dir"
    )
    assert not unused, f"translated but never shown: {unused}"


def _split_arguments(call: str) -> list[str]:
    """Split an argument list on top-level commas."""
    parts, depth, current = [], 0, ""
    in_string = None
    for char in call:
        if in_string:
            current += char
            if char == in_string:
                in_string = None
            continue
        if char in "\"'`":
            in_string = char
        elif char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
        elif char == "," and depth == 0:
            parts.append(current)
            current = ""
            continue
        current += char
    parts.append(current)
    return parts


# ── confirmed-hazard response plans ──


@pytest.mark.safety
def test_the_response_plan_is_described_never_offered_as_a_control() -> None:
    # A risk page is the last place to put a control that operates a valve.
    # The plan is read, and `dispatched` is reported rather than toggled.
    body = JS_CODE[JS_CODE.index("function responsePlan(") :]
    body = body[: body.index("\n}")]
    assert 'el("button"' not in body, "the response plan renders no control"
    assert "addEventListener" not in body
    assert "method:" not in body
    assert "plan.dispatched" in body


@pytest.mark.safety
def test_prepared_and_done_are_never_the_same_words() -> None:
    # "Prepared" and "done" are one careless reading apart, and the difference
    # is whether a valve moved. Each has its own sentence in both languages.
    for key in ("response_done", "response_prepared", "response_not_dispatched"):
        assert key in I18N["en"] and key in I18N["ar"], key
    prepared = I18N["en"]["response_prepared_detail"].lower()
    assert "not been sent" in prepared
    assert "not be sent" in prepared
    assert "nothing has been sent" in I18N["en"]["response_not_dispatched"].lower()


@pytest.mark.safety
def test_a_blocked_action_is_shown_rather_than_omitted() -> None:
    # A plan that silently drops what it will not do reads as a complete plan.
    body = JS_CODE[JS_CODE.index("function responsePlan(") :]
    body = body[: body.index("\n}")]
    assert "plan.blocked" in body
    assert "response_blocked" in body


@pytest.mark.safety
def test_a_confirmed_hazard_with_no_plan_is_reported_as_a_problem() -> None:
    # A confirmation authorises a response. That none is recorded is itself
    # worth reporting, not a blank section.
    assert "no_plan_title" in JS_CODE
    assert "no_plan_detail" in JS_CODE


def test_the_periodic_refresh_does_not_wipe_an_answer_the_user_asked_for() -> None:
    # The refresh exists to keep live data current. A test run's result is not
    # live data, and wiping it a few seconds after the click makes the button
    # look broken — the same failure as the approval confirmation that used to
    # flash and vanish.
    boot = JS_CODE[JS_CODE.index("async function boot()") :]
    # The fallback poll checks it...
    assert "if (state.holdRefresh) return;" in boot
    # ...and so does the live stream, which is now the primary path. A rule
    # enforced on one of the two would be enforced on neither in practice.
    assert "function refreshUnlessHeld()" in JS_CODE
    unless_held = JS_CODE[JS_CODE.index("function refreshUnlessHeld()") :]
    assert "if (state.holdRefresh) return;" in unless_held[: unless_held.index("\n}")]
    # Navigating away releases the hold, so a held view cannot go stale forever.
    route = JS_CODE[JS_CODE.index("async function route()") :]
    route = route[: route.index("\n}")]
    assert "state.holdRefresh = false" in route


def test_every_enumerable_key_has_a_label_in_both_languages() -> None:
    """Keys the static scan cannot see.

    The builder writes `t(`cap_${capability}`)`, which no regex over the source
    can resolve — so `test_every_translation_key_used_in_the_ui_exists` passed
    while all thirty-one capability dropdowns would have rendered raw keys. The
    families are enumerable, so they are checked against the registry itself
    rather than against what the source happens to spell out.
    """
    from syltra_contracts import ContextType
    from syltra_contracts.capability_definitions import CAPABILITY_DEFINITIONS
    from syltra_security import Permission, Role

    expected = {f"cap_{c.replace('.', '_')}" for c in CAPABILITY_DEFINITIONS}
    expected |= {f"context_{c.value.lower()}" for c in ContextType}
    # Roles and permissions are built the same way — `t(`role_${...}`)` — and
    # were missed by the first version of this test, which is how SUPPORT and
    # four permissions reached a dropdown as raw keys.
    expected |= {f"role_{r.value.lower()}" for r in Role}
    expected |= {f"permission_{p.value}" for p in Permission}
    for language in ("en", "ar"):
        missing = sorted(expected - set(I18N[language]))
        assert not missing, f"{language} has no label for: {missing}"
