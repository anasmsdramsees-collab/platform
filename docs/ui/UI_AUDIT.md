# Platform UI audit against the SYLTRA UI/UX Guidelines

- Audited: 2026-08-19
- Against: `Identity/SYLTRA_Platform_UI_UX_Guidelines.md` v1.0
- Subject: `apps/local-console/` — the SYLTRA web platform UI
- Out of scope: the Next.js marketing site in `src/` (guidelines §2 excludes the
  public website), mobile, panels, TV.

## What was audited

The console was built in Phase 7 against platform spec §28, which asked for
"a minimal local operations console". It predates these guidelines. 811 lines
across four files.

The honest summary: **the RTL and safety-communication foundations are sound and
worth keeping; the entire visual layer is off-brand and must be replaced by
tokens.**

## What already complies

Worth stating, because it determines how much is rebuilt versus retained.

| Guideline | Evidence |
|---|---|
| §10.2 logical properties, no encoded left/right | Every direction-sensitive rule uses `margin-inline`, `padding-inline`, `border-inline`, `inset-inline`, `text-align: start`. A test asserts no physical property appears. |
| §10.2 mirrored navigation | Arrow-key tab navigation inverts under `dir="rtl"`. |
| §0 rule 8, §14 — status by more than colour | Every status carries a text badge beside its colour. |
| §0 rules 3, 4 — no Home Assistant exposure | No HA entity, service name, or frontend asset appears. A test sweeps for them. |
| §22 visible focus | `:focus-visible` with a 3px ring on every interactive element. |
| §15 inferred vs confirmed | Advisory risk cases are labelled advisory in both languages. |
| §21 no one-click safety action | The console exposes no actuator control at all; its only mutations are approve, reject and feedback, each through the policy gate. |
| §20 partial states | Empty, loading and error states exist per view. |

## Conflicts

Severity: **S1** blocks Phase UI-0 acceptance · **S2** must be fixed in UI-0 ·
**S3** belongs to a later UI phase · **S4** blocked on an external decision.

### Colour system (§6)

| # | Conflict | Severity | Resolution |
|---|---|---|---|
| C1 | Accent is `#4da3ff`, a generic blue, not Electric Cyan `#2BC4D9` | S2 | Replaced by `--accent` from tokens |
| C2 | Background `#0f1216`, surface `#171c22`, border `#2a323c` — none match the Graphite scale | S2 | Replaced by the Graphite ramp |
| C3 | Text is cool grey `#e8edf2`; the Sand palette is entirely absent | S2 | `--text-primary: #F7F4EC` |
| C4 | `--ok: #3ddc97` — a green-teal used as a **primary** status colour | **S1** | Green is not a brand colour (§6, rule 16). Now semantic-only `--status-success: #22C55E` |
| C5 | Warning `#f5b445` and critical `#ff3b3b` are approximations | S2 | `#F59E0B` / `#EF4444` |
| C6 | No `--status-unknown` or `--status-offline`; unknown rendered as plain muted text | S2 | Added; §14 requires unknown and offline to be explicit, never hidden |
| C7 | 18 raw hex values hardcoded in the stylesheet | **S1** | All 18 replaced by tokens; `console.css` now carries no palette and no `prefers-color-scheme` override |

### Typography (§7)

| # | Conflict | Severity | Resolution |
|---|---|---|---|
| C8 | `system-ui` stack; neither IBM Plex Sans Arabic nor Inter requested | S2 | Correct stacks in `typography.css` |
| C9 | No type scale — ad-hoc `rem` sizes | S2 | The full §7.2 scale as tokens |
| C10 | No tabular numerals; §7.1 requires them for metrics, energy, temperature, counts | S2 | `--font-numeric` with `font-variant-numeric: tabular-nums` |
| C11 | Technical identifiers rendered without direction isolation | S2 | `.identifier` + `<bdi>` helper (§7.3, §10.2) |
| C12 | Font files are not vendored, and the hub may have no internet (§4.2 local-first) | **Closed** | Owner approved vendoring on 2026-08-21. IBM Plex Sans Arabic, Inter and IBM Plex Mono ship with the console at four weights each, all OFL 1.1, licence texts beside the files and in `THIRD_PARTY_NOTICES.md`. Served from the hub, never from a CDN. Tests fail if a declared family has no file, a used weight has no file, a family has no licence, or a `@font-face` names a remote URL |

### Spacing, radius, elevation, density (§8)

| # | Conflict | Severity | Resolution |
|---|---|---|---|
| C13 | One `--space: 1rem`, no scale | S2 | The 4px scale, 10 steps |
| C14 | One `--radius: 10px` | S2 | 6 / 10 / 14 / 18 / 999 |
| C15 | No elevation tokens; §8.3 wants borders before shadows | S2 | Three shadow tokens, documented for popovers/dialogs/menus only |
| C16 | No density modes; §8.4 requires Comfortable and Compact | S2 | `[data-density]` switching control heights and cell padding |

### Motion (§19)

| # | Conflict | Severity | Resolution |
|---|---|---|---|
| C17 | No motion tokens | S2 | 120 / 180 / 240ms |
| C18 | `prefers-reduced-motion` not honoured | **S1** | §22 requires it |

### Themes (§6.3, §6.4)

| # | Conflict | Severity | Resolution |
|---|---|---|---|
| C19 | Light theme via `prefers-color-scheme` only; no explicit control | S2 | `[data-theme]` with system default, dark as the primary experience |
| C20 | Dark is not treated as primary — the light palette is the first-declared | S2 | Dark declared on `:root`; §6.3 says dark is the primary platform experience |

### Structure and tooling (§24, §25)

| # | Conflict | Severity | Resolution |
|---|---|---|---|
| C21 | None of the six required token outputs exist | **S1** | Built in UI-0 |
| C22 | No component catalogue (rule 19) | **S1** | Living catalogue; see ADR-008 |
| C23 | No design-system directory | S2 | `apps/local-console/src/design-system/` per §24 |

### Navigation and shell (§4, §9.2)

| # | Conflict | Severity | Resolution |
|---|---|---|---|
| C24 | Nine horizontal tabs, not a persistent sidebar | S3 | Phase UI-1 |
| C25 | Missing nav items: Properties, Rooms, Automations, Energy, Installations, Users and Roles | S3 | Phase UI-1 |
| C26 | Navigation is not role-filtered (§3, §4) | S3 | Phase UI-1 — backend roles already exist in `libs/security` |
| C27 | No workspace or property selector | S3 | Phase UI-1 |
| C28 | No 264px/72px sidebar geometry or 64px top bar | S3 | Phase UI-1 |

### Components (§12, §13)

| # | Conflict | Severity | Resolution |
|---|---|---|---|
| C29 | Control height ~30px; §12.1 recommends 44px, §22 requires 24px minimum | **S1** | `--control-height-*` tokens; 44px comfortable |
| C30 | No shared primitives — every element is styled ad hoc | S2 | Primitive layer in UI-0, full set in UI-1 |
| C31 | None of the 13 domain components exist (§13) | S3 | UI-2 onward |

### Brand assets (§5)

| # | Conflict | Severity | Resolution |
|---|---|---|---|
| C32 | Wordmark is typed text, not the approved lockup | **Partly closed** | The *symbol* is now the product's own artwork rather than a typed letter. The *wordmark* beside it stays typed: there is no vector lockup, and tracing a gradient logo would misrepresent the identity rather than close the gap |
| C33 | Favicon is the platform default | **Closed** | The product mark at 16/32/48 plus a 180px apple-touch icon, generated from `Identity/syltra-app-icon.png` on 2026-08-21. Raster is the right format here — 16, 32 and 48 are pixel grids. The SVG §5.2 also asks for still needs a vector original |
| C34 | Guidelines reference `new logo.PNG`, `instagram pp.PNG`, `sila-identity-sheet.png` — none exist in `Identity/` | **S4** | Product owner to supply |
| C35 | The eight §5.4 production SVGs do not exist | **S4** | §5.4 forbids generating them from PNGs without visual review and product-owner approval. **Not generated.** |

## Status after Phase UI-0

Phase UI-0 built the token layer, the themes, the Arabic RTL foundation, the
accessibility baseline and the component catalogue. It deliberately did **not**
redesign a single screen.

| Severity | Count | Closed in UI-0 | Remaining |
|---|---|---|---|
| S1 — blocks UI-0 acceptance | 6 | 6 | 0 |
| S2 — must be fixed in UI-0 | 18 | 18 | 0 |
| S3 — later UI phase | 6 | 5 in UI-1, 1 in UI-2 | 0 |
| S4 — blocked on an external decision | 5 | 2½ | C34, C35, and the wordmark half of C32 |

Every conflict this repository can close was closed by the end of UI-2. UI-3
and UI-4 went beyond the register: the intelligence and action screens, the
§21 critical-action pattern, and the Energy view, plus four platform defects
the audit could not have predicted because they were only visible from the
API — see `IMPLEMENTATION_STATUS.md`.

Closed in UI-0: C1–C11, C13–C23, C29, C30.
Closed in UI-1: C24–C28 (sidebar shell, the full §4 navigation, role filtering,
workspace and property selection, and the 264/72/64px geometry).
Closed in UI-2: C31 (the §13 domain components), plus the seven §17 operational
screens built on them.
Remaining: the five S4 conflicts blocked on the product owner — brand assets,
the production SVGs, and font licensing. Every conflict this repository can
close is closed.

The console was migrated onto the tokens as part of UI-0. That is not a screen
redesign — it swaps 18 hex literals and a private palette for design-system
tokens, which is precisely what the acceptance criterion "no feature component
contains hardcoded brand color" asks for. The console is a feature component,
so leaving it un-migrated would have meant claiming the criterion while failing
it. Its shell, navigation and layout are untouched and remain UI-1 work.

One caveat, stated rather than buried: **contrast is verified by computation,
not by eye.** `libs/design-tokens` checks all 44 visible pairs per theme against
the WCAG 2.2 formulas, and the catalogue recomputes them in the browser from
what was actually painted. Neither substitutes for the §28 manual checks
(screen reader, 200% zoom, RTL walkthrough), which remain outstanding.

### Defects the catalogue surfaced

Building the catalogue was not a formality. Rendering every component at every
size, in both themes and both directions, found defects that reading the
stylesheets did not.

| Defect | Effect | Fix |
|---|---|---|
| Tables had no scroll container | A 621px device table inside a 400px viewport was **clipped** by its card, and the far columns became unreachable — worse than a scrollbar, because nothing signalled they existed (WCAG 1.4.10 reflow) | `.table-scroll`, keyboard-reachable, with a `--pinned-header` modifier that gives the wrapper a real scrollport |
| The skip link was `position: absolute` | It resolves against the initial containing block, so once the page had scrolled it was focusable but off-screen — the exact failure a skip link exists to prevent | `position: fixed` |
| The console's own badge separated advisory from confirmed by **colour alone** | The product's most important distinction (§15), invisible to a colour-blind user and under forced colors. The console had its own `.badge`, so the design system's dashed-border cue never reached it | One badge, in the design system: advisory dashed, confirmed solid, shadow dotted |
| `--grid-gap` and `--type-title-size` were referenced but never defined | Silent — the property falls back to its initial value and the component looks *nearly* right | Corrected, plus a test that fails on any `var()` naming a token no generated stylesheet defines |

All four have regression tests.

## Blockers requiring a product-owner decision

Recorded rather than worked around.

1. **Approved brand assets.** `Identity/` contains the primary lockup, a UI
   reference sheet, two SYLTRA tv assets, `sila-icon.png` and
   `syltra-app-icon.png`. The last two are explicitly excluded from platform use
   by §5.1. The referenced `new logo.PNG`, `instagram pp.PNG` and
   `sila-identity-sheet.png` are absent.
2. **Production SVGs (§5.4).** Eight files are required before production UI is
   marked complete, and §5.4 explicitly forbids automatic generation from the
   PNGs. The console therefore ships typed text until they arrive.
3. **Font licensing.** IBM Plex Sans Arabic is OFL and vendorable. Inter is OFL.
   Both must be vendored as WOFF2 rather than fetched, because the hub may have
   no internet (§4.2). This needs a decision on repository size and licence
   notices before the files land.

## Retained by deliberate decision

- **No build step.** ADR-007 chose static HTML/CSS/JS because the console is
  served by a constrained hub. §24's structure is labelled "suggested", and rule
  19 says "Storybook **or equivalent**". ADR-008 records following the mandated
  token file structure while keeping the no-build constraint.
- **The existing RTL implementation.** It already satisfies §10.2 and is tested.
  UI-0 extends it rather than replacing it.
