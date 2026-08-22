# The SYLTRA design system and console

For the next person who has to change this UI.

Governed by `SYLTRA_Platform_UI_UX_Guidelines.md`. Where this document and the
guidelines disagree, the guidelines win and this document is out of date.

## What exists

```text
apps/local-console/
├── src/design-system/
│   ├── tokens/tokens.json        the single source of truth
│   ├── tokens/tokens.css         generated
│   ├── tokens/motion.css         generated
│   ├── themes/dark-theme.css     generated — dark is declared on :root
│   ├── themes/light-theme.css    generated
│   ├── typography/typography.css generated
│   ├── foundation.css            bidirectional layout, a11y baseline, text utilities
│   ├── primitives.css            §12 core components
│   ├── shell.css                 §9.2 application shell
│   └── domain.css                §13 domain components, §20 states, §21 confirmation
└── static/
    ├── index.html                the shell, as markup
    ├── console.js                everything else
    ├── i18n.json                 every user-visible string, en + ar
    └── catalogue/                the living style guide
```

**The console has no stylesheet of its own.** That is deliberate: it is what
makes "no feature component contains a hardcoded brand colour" true by
construction rather than by review. If you find yourself wanting one, the thing
you are building belongs in the design system.

## Changing a colour, a size, or a spacing step

Edit `tokens/tokens.json`, then:

```bash
make tokens
```

A test fails if the checked-in CSS has drifted from the JSON, so you cannot
forget. `make contrast` reports the WCAG ratio of every token pair in both
themes and exits non-zero if any pair fails — the same check runs in CI.

## Adding a component

1. Add the CSS to `primitives.css` (a §12 core component), `shell.css` (layout)
   or `domain.css` (something that knows what SYLTRA is about).
2. Add a specimen to `static/catalogue/index.html`. This is not optional: a
   test fails if the design system defines a class the catalogue never shows.
   A catalogue that documents most of the system is worse than none, because it
   looks like a complete inventory.
3. Use tokens for every value. A test fails on a hex literal, and on a `var()`
   naming a token no generated stylesheet defines.

## Adding a screen

- Add an entry to `NAV` in `console.js` with the permission it needs.
- Every user-visible string goes through `t()` and into `i18n.json` in **both**
  languages. A test fails on a missing key, and on a key nothing reads.
- Read the API's real field names. `test_console_contract.py` asserts that
  every field the console reads exists in the response — three screens once
  shipped reading fields that do not exist, and every test passed because the
  tests only checked the console against itself.
- Implement the §20 states. Tests assert every primary screen can report a
  failure and can report having nothing to show.

## Rules that are enforced, not just documented

| Rule | Where it is enforced |
|---|---|
| No hardcoded colour outside the tokens | `test_the_shared_stylesheets_hold_no_hex_colours` |
| Every token pair meets its contrast bar | `libs/design-tokens`, both themes |
| Logical properties only — Arabic mirrors from `dir` alone | `test_layout_is_written_in_logical_properties_only` |
| Both themes define exactly the same tokens | `test_the_two_themes_define_exactly_the_same_tokens` |
| Every component has a catalogue specimen | `test_the_catalogue_renders_every_component_the_system_defines` |
| Advisory, confirmed and shadow differ by more than colour | `test_advisory_confirmed_and_shadow_differ_by_more_than_colour` |
| Navigation filters on permissions, never on a role name | `test_navigation_is_filtered_by_permission_not_by_role_name` |
| Hiding a control is not authorization | `services/api-gateway/tests/test_identity.py` |
| The audit view can never write | `test_the_audit_trail_offers_no_way_to_change_it` |
| The console names only real capabilities | `test_every_capability_the_console_names_exists` |

## What the tests cannot check

`docs/ui/ACCESSIBILITY_VERIFICATION.md` records what has been checked and how.
Guidelines §28 keeps these as manual checks, and they are still outstanding:

- a screen reader walkthrough of the primary workflows;
- 200% browser zoom on every screen;
- an Arabic reading pass by someone who reads Arabic — the strings are
  translated and the layout mirrors, but nobody has read it for tone;
- Windows high-contrast mode. The rules are written and the CSSOM confirms
  they load, but nobody has looked at it.

Focus-ring *rendering* is also unverified: `:focus-visible` needs real user
focus, which a backgrounded automation pane does not grant. The rules are
present and load correctly; whether they look right is a manual check.

## Running it

```bash
make console
```

Prints one development token per role, so a role-aware change can actually be
checked as each role. The catalogue is at `/console/catalogue/` and needs no
token — it shows the design system, not a home.
