# ADR-007: A self-contained local console, not a second Node application

- Status: Accepted
- Date: 2026-08-19
- Deciders: Implementation engineering (Phase 7)

## Context

Spec §7.8 calls for a "minimal local operations console for the MVP" — a
responsive web UI in Arabic RTL and English LTR, with no Home Assistant branding
and no re-skinned Home Assistant frontend. Spec §28 lists the views it must show.

The obvious instinct is a React or Next.js application. This repository already
contains a Next.js marketing website under `src/`, so the tooling exists.

Three considerations argued against it:

1. **It runs on a hub, not a laptop.** The console is served by the SYLTRA Hub
   (spec §6.2) to whoever is on the household network. A Node runtime, a build
   step and a `node_modules` tree are real cost on constrained hardware, for a
   handful of operational views.
2. **The platform is otherwise Python-only.** Adding a Node build to
   `make bootstrap` means every developer and every CI run needs both
   toolchains, and the container images grow accordingly.
3. **Confusion with the marketing site.** `src/` is the public SYLTRA SMART
   website. A second Next.js app in the same repository invites exactly the
   coupling ADR-003 was written to prevent.

## Decision

Build the console as **self-contained HTML, CSS and vanilla JavaScript**, served
directly by the API Gateway from `apps/local-console/`. No build step, no
bundler, no framework.

Specifically:

- one HTML document per view, sharing one stylesheet and one small JS module;
- translations as a JSON dictionary loaded at runtime, so adding a language is a
  data change;
- `dir="rtl"` and CSS logical properties (`margin-inline-start`,
  `padding-block`, `border-inline-end`) rather than physical ones, so Arabic
  layout is genuine mirroring and not a stylesheet fork;
- no external CDN or font fetches — the hub may have no internet (spec §4.2).

## Consequences

- `make bootstrap` stays Python-only; the console ships inside the API Gateway
  image with no additional build stage.
- The console is inspectable: an installer debugging a hub can read the source
  in a browser, which suits a device that lives in someone's home.
- Complex interactive views (live charts, drag-and-drop dashboards) would be
  painful to build this way. The MVP console has none, and if the product later
  needs them, this ADR is superseded rather than stretched.
- Accessibility is hand-rolled rather than inherited from a component library,
  so it is tested explicitly (landmarks, labels, focus order, contrast) instead
  of assumed.

## Alternatives considered

- **Next.js under `apps/local-console/`** — best developer ergonomics and the
  richest component ecosystem, but adds a Node toolchain to a Python platform
  and a second Next.js app to a repository that already has one.
- **Extending the existing `src/` website** — rejected outright. The marketing
  site is public and internet-facing; the console is local, authenticated, and
  shows household data. They must not share a deployment or a codebase.
- **Serving the Home Assistant frontend** — prohibited by spec §30 and §4.9.
