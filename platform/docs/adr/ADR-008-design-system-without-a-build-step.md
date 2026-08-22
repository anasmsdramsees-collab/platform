# ADR-008: A design system and component catalogue without a build step

- Status: Accepted
- Date: 2026-08-19
- Deciders: Implementation engineering (Phase UI-0)
- Supersedes nothing; extends ADR-007

## Context

The SYLTRA UI/UX Guidelines require (rule 19) "a Storybook or equivalent
component catalogue", and §24 suggests a directory structure —
`src/app/`, `src/components/`, `src/features/` — that reads as a React
application.

ADR-007 chose static HTML, CSS and vanilla JavaScript for the console because it
is served by a SYLTRA Hub: a constrained device already running Home Assistant, a
database, a message broker and eight Python services. Adding a Node runtime, a
bundler and a `node_modules` tree costs real memory and disk there, and adds a
second toolchain to `make bootstrap`.

Storybook specifically would add a development-only dependency tree larger than
the entire platform it documents.

## Decision

Follow the guidelines' **mandated outputs** exactly, and its **suggested
structure** where it does not require a framework.

Concretely:

1. **The six required token files are built exactly as §24 specifies**, under
   `apps/local-console/src/design-system/tokens/` and `/themes/`:
   `tokens.json`, `tokens.css`, `dark-theme.css`, `light-theme.css`,
   `typography.css`, `motion.css`.
2. **`tokens.json` is the single source of truth.** The CSS files are generated
   from it by a small Python script and checked in. A test regenerates them and
   fails if the checked-in files have drifted — the same drift guard already used
   for the JSON Schemas in `contracts/`.
3. **The component catalogue is a living style guide**: a static page served by
   the API Gateway at `/console/catalogue/`, rendering every primitive in both
   themes, both directions, and every state §25 lists. It is inspectable in a
   browser on the hub itself, which Storybook would not be.
4. **Components are CSS classes plus semantic HTML**, not framework components.
   The catalogue renders the same classes the console uses, so a component
   cannot drift from its documentation.

## Consequences

- `make bootstrap` stays Python-only; the console ships inside the API Gateway
  image with no build stage, as ADR-007 intended.
- The catalogue is available on a commissioned hub, not only on a developer
  machine — genuinely useful when an installer is debugging appearance on site.
- **Cost:** no automatic prop tables, no interaction testing add-on, no visual
  diffing out of the box. Visual regression is therefore built explicitly in
  Phase UI-6 rather than inherited.
- **Cost:** a component's variants are documented by hand in the catalogue page.
  A test asserts every token defined in `tokens.json` appears in the catalogue,
  so tokens cannot be added without being shown.
- If the platform later grows a genuine application framework — a fleet console
  running on a server rather than a hub, for example — this ADR is superseded
  rather than stretched.

## Alternatives considered

- **Storybook with React.** Best-in-class documentation and the guidelines' first
  suggestion. Rejected on hub cost: it would make the documentation tooling
  heavier than the product, and force a Node runtime into a Python platform.
- **Storybook for HTML.** Lighter than the React setup, but still a Node
  toolchain and a `node_modules` tree for a nine-view console.
- **Extending the existing Next.js site in `src/`.** Rejected outright, as in
  ADR-007: that site is public and internet-facing, while the console is local,
  authenticated and shows household data. They must not share a deployment.
