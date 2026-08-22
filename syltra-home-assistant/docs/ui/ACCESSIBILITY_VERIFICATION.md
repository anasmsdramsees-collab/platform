# Accessibility verification record

What has actually been checked on the SYLTRA console, how, and what still needs
a person. Written so the next reviewer does not have to re-derive it, and so
nobody mistakes "the tests pass" for "someone has used it".

Guidelines §22 and §28. Last run: Phase UI-6.

## Verified automatically, on every run

These are pytest assertions and fail the build.

| Check | Where |
|---|---|
| Every token pair meets its contrast bar, both themes | `libs/design-tokens` — 44 pairs per theme, WCAG 2.2 formulas |
| No colour literal outside the tokens | `test_the_shared_stylesheets_hold_no_hex_colours` |
| Logical properties only — Arabic mirrors from `dir` alone | `test_layout_is_written_in_logical_properties_only` |
| Focus is never removed | `test_keyboard_focus_is_always_visible` — no `outline: none` anywhere |
| Minimum target size tokens present | `test_interactive_targets_carry_a_minimum_size` |
| Links filling a table cell reach 24px | `test_a_link_that_fills_a_table_cell_meets_the_minimum_target_size` |
| No heading level is skipped | `test_no_screen_skips_a_heading_level` |
| Reduced motion honoured | `test_reduced_motion_is_honoured` |
| Forced colors keeps boundaries | `test_forced_colors_keeps_boundaries_visible` |
| Status is never colour alone | `test_status_is_never_carried_by_colour_alone`, and advisory/confirmed/shadow differ by border style |
| Every string is translated, both languages | `test_every_translation_key_used_in_the_ui_exists` and its mirror |

## Verified by driving a real browser

Repeatable, but not automated in CI — a browser is needed. Re-run these after
any layout change.

| Check | Method | Result |
|---|---|---|
| Nine structural a11y rules over all 13 routes, both languages | duplicate ids, unlabelled controls, nameless controls, heading order, landmarks, unhidden icons, target size, table headers, list structure | **clean** |
| Reflow at 200% zoom (720px viewport) | every route, measuring clipping and sideways scroll | **clean** — only data tables exceed the viewport, each inside a scrollable, labelled, keyboard-reachable wrapper; the page itself never scrolls sideways |
| Reflow at 400px | as above | **clean**, same result |
| Accessible names, roles and order | accessible-name computation excluding `aria-hidden`, read in document order | **clean** — navigation announces "Overview", "Properties", … with no icon glyph; no control has a symbol-only name |
| RTL geometry | sidebar side, current-page marker, directional vs universal icons, identifier and chart direction, overflow | **clean** at 1440px and 768px |
| Keyboard navigation | focus order, arrow keys in the sidebar, Home/End, no route change on focus, no trap | **clean** |
| Role-based views | signed in as all five roles | **correct** — see `IMPLEMENTATION_STATUS.md` |

## Still needs a person

None of these can be automated, and none has been done. §27 criterion 12 is
not met until they are.

1. **A screen reader walkthrough** of the primary workflows — NVDA or VoiceOver,
   someone listening. The structure a screen reader consumes is verified above;
   whether it *reads well* is a different question, and the answer is unknown.
2. **An Arabic reading pass by someone who reads Arabic.** Every string is
   translated and the layout mirrors correctly. Nobody has read it for tone,
   register, or whether a sentence lands the way it should.
3. **Windows high-contrast mode.** The `forced-colors` rules are written and
   the CSSOM confirms they load. Nobody has looked at the result.
4. **Focus-ring rendering.** `:focus-visible` requires real user focus, which a
   backgrounded automation pane does not grant, so the rules were verified as
   present and correctly parsed rather than as painted. Whether the ring is
   visible enough on each surface is a human judgement.
5. **Pixel regression.** Geometry and computed styles are measured in dark,
   light, Arabic, English and at 768px, which catches layout breakage. It does
   not catch a component that renders the wrong colour on the right geometry.
   That needs a baseline someone has approved.

## How to re-run the browser checks

```bash
make console
```

Then open the console and the catalogue side by side. The scripts used for the
sweeps are not committed: they were written against the browser automation
available at the time, and a stale script that silently checks the wrong thing
is worse than none. What each check *asserts* is listed above, which is the
part worth keeping.
