# SYLTRA — the gaps

Everything known to be missing, unverified, or untrue about this platform, in
one place. Organised by **who can close it**, because that is what decides what
happens next.

Compiled by inspecting the tree, not by recalling the build. Where a figure
appears it was checked. Last swept at commit `f64096a`.

> Read §1 first. It is the only section describing things that might already be
> wrong rather than merely absent.

---

## 1. Unverified — the things that could already be broken

These are not missing features. They are claims the test suite makes that
nothing outside this repository has ever checked.

### 1.1 The Home Assistant boundary has never met a real Home Assistant

**The most important line in this document.**

Every integration test runs against a **mock Home Assistant written by this
project**. The mock encodes what we believe HA's WebSocket API sends: message
shapes, event names, registry payloads, `state_changed` structure.

If any of those beliefs is wrong, **every test still passes** and the real thing
fails on first contact.

This is not hypothetical. The exact failure mode occurred repeatedly during the
UI phases — three screens read fields that did not exist, and the approve button
returned 404 for every recommendation, all while the suite was green, because
the tests checked the code against itself rather than against the thing it talks
to.

The Edge Agent is that same shape of code, against a boundary nobody has tested.

*Closing it:* run the Edge Agent against a real Home Assistant with real devices
for a day, in observe-only mode, and read the unmapped-capability counter.

### 1.2 Nothing has run in a real home

Every event in every test is synthetic. The simulator is deterministic by
design. A real home has flaky Zigbee, devices that lie about their state, clocks
that drift, and a person who unplugs something.

*Closing it:* the pilot in `docs/pilot/PILOT_CHECKLIST.md`, behind
`DispatchMode.OBSERVE_ONLY`.

### 1.3 Nothing has run at scale

One home. Nine devices. Roughly three hundred events. No test covers a year of
history, a hundred devices, or a database that has grown.

TimescaleDB was deliberately deferred (ADR-005) on the reasoning that MVP
volumes do not need it. That reasoning has never been tested against real
volume.

*Closing it:* a soak run with a year of synthetic history at realistic device
counts, watching twin rebuild time and query latency.

### 1.4 Four accessibility checks need a human

Automation covers contrast, target size, heading order, landmarks, labelling,
reflow at 200% and 400%, and the accessible-name tree. What it cannot cover:

| Check | Status |
|---|---|
| Screen reader walkthrough | **never run** |
| Arabic reading pass for tone and register | **never run** — strings are translated and the layout mirrors; nobody has read it as prose |
| Windows high-contrast mode | rules written and confirmed loaded; nobody has looked at it |
| Focus-ring visibility | rules present and parsed; `:focus-visible` needs real user focus, which a backgrounded automation pane cannot grant |

Recorded in `docs/ui/ACCESSIBILITY_VERIFICATION.md`.

### 1.5 No pixel regression baseline

Geometry and computed styles are measured in dark, light, Arabic, English and at
768px, which catches layout breakage. It does **not** catch a component
rendering the wrong colour on correct geometry.

*Closing it:* a baseline somebody has looked at and approved.

---

### 1.6 The offline claim is proven in-process, not as a deployed stack

Spec §0 rule 4 says loss of internet must not stop local control. The build
honours it structurally: no service calls an external host, the console loads no
CDN asset or remote font, the models are trained locally and no pretrained
weights are fetched, and `services/cloud-connector/` is empty.

`tests/safety/test_offline_operation.py` now tests it rather than asserting it.
The guard there models an unplugged router rather than a disabled socket layer —
loopback keeps working, everything else fails with ENETUNREACH and a dead
resolver — and the control path is built and run inside it. Each test asserts
twice: that the device really changed, and that nothing *reached* for the
internet at all. The second is the one that matters, because a component that
tries a cloud call and tolerates the timeout would pass the first.

What is still unproven is the same claim about the **deployed stack**. Those
tests run in one process against the mock Home Assistant, with no containers, no
NATS and no PostgreSQL. They show the logic needs no internet. They do not show
that six containers on a real host behave the same way when the interface goes
down — which is the form of the claim that a pilot actually depends on, and
which shares its root with §1.1.

Two things sit outside the platform's control and no test will change them:
Home Assistant integrations that are themselves cloud-based will stop when the
line drops, and a NOTIFY step routed to mobile push needs the internet to reach
a phone. Both are properties of what you connect, not of SYLTRA.

*Closing it:* `make up`, take the host's network interface down, drive a control
path through the API, and confirm it completes.

---

## 2. Needs a decision from you

Nothing here can proceed without a product judgement. Each is blocked, not
forgotten.

### 2.1 May a confirmed hazard operate an actuator?

A confirmed gas alarm currently **notifies** and **prepares** — identifies the
valve, verifies it can be reached, computes the command — and stops. Execution
is unbuilt, and structurally unreachable from that path.

Spec §0 rule 9 requires explicit approval before anything operates a real safety
actuator. Everything needed to decide is now visible: which valve, whether it
answers, exactly what would be sent.

This also blocks UI §27 criterion 8 (critical controls use confirmation and
verification) — the confirmation pattern is built and waiting for an action to
attach to.

### 2.2 Scope for Installations and Users and Roles

Both have navigation entries marked unavailable. Neither has a backend.

Two UI-5 acceptance criteria stay unmet until user management exists: *permission
changes require confirmation and audit reason*, and *commissioning stages are
recoverable*.

### 2.3 The Cloud Connector

Spec §14.11 gives it MVP responsibilities — disabled by default, an export
allowlist, offline queueing, payload redaction. `services/cloud-connector/`
contains a `.gitkeep`.

Not critical: the platform's promise is that local control never depends on the
cloud, and a connector that does not exist is trivially disabled. But it is a
specified MVP component that is absent, and it is why one of §29's fourteen
required metrics (*cloud connector status*) has no source.

### 2.4 Brand assets

Five conflicts from the UI audit (C12, C32–C35) blocked on you:

- the eight §5.4 production SVGs — the guidelines forbid generating them from
  the PNGs without visual review, so the console renders a typed wordmark;
- a font-licensing decision, so IBM Plex Sans Arabic and Inter can be vendored
  rather than named and degraded to system fonts;
- three referenced assets that do not exist in `Identity/`.

### 2.5 Two automation questions

- Is the **visual builder** worth building? Automations are created through the
  API today; the screen lists, tests and switches them, and says the editor is
  missing.
- Are **scheduled triggers** ("at 7pm") in scope? They need a clock source in
  the evaluation loop, which is a decision about who owns time in this platform.

### 2.6 Energy over time

The Energy screen shows current power, per-device breakdown where a device
meters it, anomalies and coverage. It shows no trend, no baseline comparison and
no cost, because the platform records power as it is read and keeps no
aggregation — and §17.11 forbids estimating any of them.

*Closing it:* a time-series endpoint, which is also what §27 criterion 9
(charts) needs.

---

## 3. Needs a person, not a decision

- **The pilot itself** — `docs/pilot/PILOT_CHECKLIST.md` and its sign-offs.
- **The four manual accessibility checks** in §1.4.
- **Reading the pilot week's refused commands.** The observe-only mode records
  every command not sent; the deliverable is somebody reading them, not counting
  them.

---

## 4. Known engineering gaps

Scoped, understood, nobody blocked on a decision.

| Gap | Consequence | Size |
|---|---|---|
| `contracts/openapi/` is empty | Spec §21 requires an OpenAPI specification as an artifact. FastAPI serves it live at `/v1/openapi.json`; nothing exports a versioned copy the way `make contracts` does for JSON Schemas | small |
| `contracts/examples/` is empty | Spec §8 places contract examples here; the JSON Schemas exist without worked examples | small |
| Update and rollback is designed, not implemented | `docs/architecture/DEPLOYMENT.md` describes the sequence. Spec §22 Phase 8 asked for a *design*, so this is beyond what the MVP required — but a pilot hub will eventually need updating | medium |
| Feedback Service has no metrics module | Not one of §29's fourteen, but it is the one remaining service with no instrumentation | small |
| The console polls every 15 seconds | `/v1/stream` exists and nothing uses it. Polling is simple and works; a pilot watching live state would prefer the stream | medium |

---

## 5. Structural divergence from spec §8

Directories the specification's layout defines, which exist as placeholders
because the content settled elsewhere. Harmless, but an empty `models/exported/`
implies models are exported there and they are not.

| Empty directory | Where the content actually is |
|---|---|
| `models/definitions`, `models/training`, `models/evaluation`, `models/exported` | `services/adaptive-engine/src/` |
| `simulator/devices`, `simulator/scenarios`, `simulator/fixtures` | `simulator/src/syltra_simulator/` |
| `infrastructure/docker` | a `Dockerfile` per service |
| `contracts/openapi`, `contracts/examples` | nothing — see §4 |
| `services/cloud-connector` | nothing — see §2.3 |

*Closing it:* either move the content, or delete the placeholders and note the
divergence in `SYSTEM_OVERVIEW.md`. The second is probably right; the layout in
§8 was a suggestion and the packages settled where a Python workspace wants
them.

---

## 6. The failure pattern worth remembering

Not a gap. The thing most likely to produce the next one.

Every significant defect found in this build shared a shape: **a test that
checked the code against itself.**

- The MVP was declared complete, with 739 passing tests and an 18/18 definition
  of done, while a user could not approve a single recommendation — the approve
  endpoint returned 404 for every one of them, because nothing ever created the
  policy decision it looked for. Every test drove the services in-process.
- Three console screens read API fields that did not exist. Green suite.
- `light.power` was summed as a wattage. It is a boolean on/off switch, and the
  meter-coverage figure it produced claimed twice the real coverage.
- `light.on` was read for the lights-on count. It is not a capability the
  platform defines, so the count was always zero.
- Forty metrics existed and were reported as complete coverage. Six of §29's
  fourteen required metrics had no source at all.
- A privacy test scanned a backup for the string `27.4`. The unencrypted
  manifest's timestamp contains `27.4` roughly one run in six hundred, so a
  correct encryption raised a leak alarm.

Four tests now exist specifically to catch that class — the console/API contract
test, the capability-name test, the live-registry metrics test, and the
dashboard-queries-what-exists test.

**The lesson for §1.1:** the Edge Agent is the last major boundary still checked
only against our own beliefs about what is on the other side.

---

## 7. What is *not* a gap

Recorded so nobody re-opens them as oversights.

- **No cloud path exists.** Deliberate. Spec §0 rule 14.
- **No free-text control of devices.** SILA takes structured intents. Spec §3.
- **`ACT_SAFETY` is held by no role.** Deliberate, enforced at import time.
- **The Risk Engine cannot confirm a hazard.** Only the Safety Governor can, and
  only from a certified alarm.
- **Automations cannot touch a critical capability.** Refused at construction.
- **Green is not a brand colour.** It appears in the status scale and nowhere
  else, enforced by test.
- **The console has no stylesheet of its own.** That is what makes "no hardcoded
  brand colour" true by construction.

---

## 8. Summary

| Category | Count | Blocked on |
|---|---|---|
| Unverified against reality | 6 | a real home, a real Home Assistant, a person |
| Awaiting your decision | 6 | you |
| Needs a person | 3 | scheduling |
| Known engineering gaps | 5 | nobody — pick them up any time |
| Structural divergence | 5 dirs | a tidy-up |

Nothing in §1 through §5 is a *critical blocker* in the sense of §32 item 18:
the platform runs, its safety guarantees hold, and its tests pass. §1.1 and §1.2
are the two that should worry you, and both close the same way — by putting it
in a real house with the dispatch switch off.
