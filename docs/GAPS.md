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

### 2.1 May a confirmed hazard operate an actuator? — **decided**

**Decided 2026-08-20, by the owner: yes, for gas.** A certified detector at its
alarm threshold is a measurement that gas is present, not an opinion about it,
and a household asked for permission is a household breathing gas while it
decides. The valve closes and the notification says so.

Built, tested and *not yet wired into the running services* — see
`docs/safety/SAFETY_CASE.md` and `tests/safety/test_gas_isolation.py`. The
direction is fixed in the type system: `valve.state` may be driven to `closed`
and to nothing else, so nothing in the platform can reopen a supply. That stays
a person's job, after the leak is found.

Still open under the same heading, and deliberately not decided by extension:

- **water** — leaks damage property rather than people, and it still prepares;
- **egress and ventilation** — neither cuts a supply;
- **siren and breaker** — they pass the deterministic-rule gate and have no
  fail-safe direction anybody has chosen.

### 2.2 Installations — **decided and built**

The owner answered the question this was blocked on: SYLTRA sells to
individuals, distributors, installers and institutions. The consequences are in
`docs/adr/ADR-010-access-is-an-invitation-not-a-consequence-of-sale.md`.

**A distributor has no access to anything.** Selling a hub does not create a
relationship with the house it went into. There is no distributor role, no
fleet view, and no telemetry leaving by default — which is why home isolation
survived a channel model that usually destroys it.

The only route in is an invitation. `SUPPORT` is SYLTRA's own technician,
granted by the owner, expiring in four hours, able to write automations and
unable to see a camera. `VIEW_CAMERA` is a permission of its own, held by
`OWNER` and `ADULT` only, and the gateway removes what a caller may not see
from the payload rather than blanking it — a null value still says *there is a
camera here*.

`Organisation` holds units a company owns and does not live in; the company is
the unit's `OWNER`, because a separate role would be the same authority wearing
a different name. `transfer_ownership` sells one in a single call: the buyer is
admitted first so the last-owner rule cannot refuse the revocation the sale
depends on, then everyone else leaves, then the previous occupants' history is
erased. Erasure is a required argument with no default, so no future edit can
quietly make it optional.

The resident is told who manages the place they live in, above the member list
— a condition of the tenancy rather than a discovery.

What is still open is commissioning: the stages of a physical install and their
recoverability. That needs a hub to install.

### 2.3 The Cloud Connector — **built, and built to refuse**

`services/cloud-connector/` held a `.gitkeep`, and the argument for leaving it
that way was decent: local control never depends on the cloud, and a connector
that does not exist is trivially disabled.

It was wrong in one direction. A component that does not exist is not a
component that refuses — it is one somebody adds in a hurry later, under a
deadline, without the refusals. It exists now in order to say no.

Four gates, each defaulting to closed: **disabled** for every household until
somebody enables it with a reason; **consent per destination**, because agreeing
to send diagnostics to an installer is not agreeing to send anything to a
manufacturer, and withdrawal empties the queue rather than draining it;
**an allowlist**, because a denylist forgets the field somebody added last week;
and **redaction** after the allowlist, since *may this field go* and *what may
it say* are different questions. Device ids become pseudonyms salted with a
value that never leaves, so a diagnostic can correlate two records from one
device and nothing downstream can join across houses.

Nothing here reaches a network — asserted on the parsed imports — and no control
path waits on it. The queue is bounded rather than durable on purpose: a
fortnight of telemetry recovered after an outage is a fortnight of household
behaviour travelling long after anybody remembered agreeing to it.

This also gives §29's fourteenth metric its source. `syltra_cloud_connector_enabled`
reads zero on a hub nobody has turned it on for, which is the evidence the
platform's central promise deserves.

### 2.4 Brand assets

Five conflicts from the UI audit (C12, C32–C35) blocked on you:

- the eight §5.4 production SVGs — the guidelines forbid generating them from
  the PNGs without visual review, so the console renders a typed wordmark;
- ~~a font-licensing decision~~ — **decided 2026-08-21**. IBM Plex Sans Arabic,
  Inter and IBM Plex Mono are vendored at four weights each under OFL 1.1, and
  the console no longer degrades to system fonts;
- three referenced assets that do not exist in `Identity/`.

### 2.5 Two automation questions — **scheduled triggers built, builder open**

**Scheduled triggers: yes, and the clock question is answered.** `AT_TIME`
stores an hour, a minute and weekdays — not a cron expression, which is a small
language, and ADR-009 refused a language for the reason it refused an
interpreter. Time belongs to the household: a wall-clock time plus an IANA
timezone, resolved when needed, so an automation saved in summer does not fire
an hour wrong all winter.

Firing once survives a restart across the hour, a clock corrected in either
direction, and a doubled daylight-saving hour, because the unit compared is the
local occurrence rather than a timestamp. Lateness is bounded so a hub restored
from a backup does not run a fortnight of evenings at once.

**A third component turned out to have no caller.** `AutomationEngine.evaluate`
was reached from the *test run* button and nowhere else: a household could
write an automation, watch a dry run say it would fire, enable it, and wait
forever. `AutomationDriver` now runs it every two seconds — slower than the
safety loop on purpose, because a light two seconds late is a light that came
on. `system_status` reports `automation_engine` degraded when that loop stops.

**The builder is built.** Four dropdowns and a time field produce the typed
graph the API accepts, with no free-text field anywhere — a builder that
smuggled a language back in through a text box would be ADR-009 reversed
quietly. The vocabulary is served from `/automations/options` rather than
copied into the console, and capabilities automations may never touch are
listed with a translated reason instead of hidden.

**And the models now propose rules, not just actions.** The adaptive engine
could always say "turn the light on now, you usually do at this hour", and said
it again the next evening; a household that accepted two hundred times had
taught the platform nothing it could keep. `/automations/proposals` turns the
routine model's strongest slots into an automation offered once.

The bar is higher than for recommending an action, because an action the model
got wrong happens once and a rule it got wrong happens every day until somebody
notices: a stronger threshold, at least three days, the weakest day's strength
reported rather than the best, nothing offered below RECOMMEND, and nothing
offered from a suspended model. The card shows the evidence — "you did this on
7 of the last 7 days" — rather than a confidence score nobody can argue with.

Accepting creates an ordinary automation through the ordinary endpoint, so it
passes every check a hand-written one passes and arrives switched off. What is
still open is version history and rollback: editing an automation replaces it,
and there is nothing to go back to.

### 2.6 Energy over time — **built**

`GET /v1/homes/{home_id}/energy/history` aggregates measured power into minute,
hour or day buckets, and the Energy screen draws it.

The design is one rule: §17.11 forbids estimating a measurement, so an hour
nothing reported in is listed under `missing` rather than drawn as zero.
`EnergyBucket` refuses to be constructed with no samples, so the rule cannot be
lost one call site at a time. Bars rather than a line, because a line has to
either join across a gap or break in a way that reads as a rendering fault.

Every bucket carries `samples` and `coverage` beside the mean — an hour measured
twice and an hour measured twelve times are not the same claim, and the sparse
one is hatched rather than merely paler, since less confidence is a state and §8
forbids carrying a state by colour alone.

Still absent, deliberately: kilowatt-hours and cost. Converting a mean of
unevenly spaced power readings to kWh is a guess; `energy.consumption` is the
capability for cumulative energy. A tariff needs effective dates and tiers, and
a cost computed from the wrong one is worse than none.

---

### 2.7 A certificate for the hub — **open**

The wall panel now keeps its own copy of itself (page, styles, script, wording,
fonts) so a hub that is restarting no longer leaves a browser error page on a
wall. That copy is a **service worker**, and a service worker only runs in a
secure context: `https://`, or `localhost`.

- A panel running **on the hub itself** (`http://localhost:8088/panel/`) gets
  full offline behaviour today. Verified in Chrome: hub stopped, page reloaded,
  panel drew itself and said it could not reach the hub.
- A panel on a **tablet on the LAN** (`http://192.168.1.20:8088/panel/`) is not
  a secure context. The service worker silently does not register, and the panel
  falls back to the browser's own HTTP cache — which the gateway now feeds with
  `max-age=300, stale-while-revalidate=2592000`. That covers a short hub restart
  and does not survive a browser that has evicted the entry.

The decision is whether the hub gets a **locally issued certificate** so LAN
panels are secure contexts. Roughly:

| Option | What it costs | What it buys |
|---|---|---|
| Leave it | nothing | LAN panels keep the weaker HTTP-cache fallback |
| Self-signed cert per hub | a trust prompt on every device, or an install step per device | full offline on every panel |
| A SYLTRA-issued cert per hub, from an internal CA | a CA to run and protect, plus renewal | full offline, no per-device prompt |
| A real certificate for a `*.hub.syltra…` name | DNS and renewal that need the internet, which the platform refuses to depend on | conflicts with §0 |

My recommendation is the second option for the pilot — a self-signed cert with a
one-time trust step during installation, which the installer is already doing —
and the third only if the pilot shows the trust step failing in real homes.
Neither is code I should write before you choose, because both change what an
installer does in somebody's house.

---

## 3. Needs a person, not a decision

- **The pilot itself** — `docs/pilot/PILOT_CHECKLIST.md` and its sign-offs.
- **The four manual accessibility checks** in §1.4.
- **Reading the pilot week's refused commands.** The observe-only mode records
  every command not sent; the deliverable is somebody reading them, not counting
  them.

---

## 4. Known engineering gaps

**None.** Every entry that stood here has been built, and the ones that mattered
each turned up something the tests could not see — which is why this section
emptying is worth less than the list of what emptying it revealed.

### Closed

| Was | Now |
|---|---|
| Update and rollback designed, not implemented | Built. Signed bundle verified before anything is written; services restarted one at a time with safety last, so a failure anywhere earlier rolls back with the safety layer untouched; automatic rollback, and a rollback that itself fails says FAILED because that is whether a person has to look. Power loss is first-class: every stage is recorded before it is attempted, and `recover()` at start-up rolls back anything that changed |
| The console polled every 15 seconds | `/v1/stream` carries change notifications with per-home sequence numbers, a heartbeat, resume-from-cursor and a `resync` when the cursor is too old to answer. The console re-reads on notification and falls back to polling only while the socket is unhealthy. Measured live: an external change reached the screen in about one second. The stream deliberately carries notifications rather than data — a second copy of every view model is a second copy that can disagree with the first |
| Nothing drove risk evaluation | `RiskDriver` evaluates every known home on a timer and carries out what that authorizes, started for the life of the app. Found while wiring the gas isolation: `evaluate` was called by the test suite and by nothing else, so the governor, the seven risk states and the shutoff were all reachable only from a caller the product did not have. `system_status` now reports the risk engine degraded when no driver is running or its loop has stalled, instead of the hard-coded `"ok"` that made a hub with nothing reading its detectors look healthy |
| `contracts/openapi/` empty | `make contracts` writes `contracts/openapi/v1.0/syltra-local-api.openapi.json` from the app itself; a test fails the build when a route changes without regenerating. The WebSocket `/v1/stream` is absent because OpenAPI 3.1 cannot describe one, and a test asserts that absence so it stays a known limitation |
| `contracts/examples/` empty | Eighteen worked examples in `contracts/examples/v1.0/`, all one evening in one synthetic home, cross-referenced by id so following `recommendation_id` from recommendation to decision to feedback works. Each re-validates through the model it came from |
| Feedback Service uninstrumented | `services/feedback-service/src/syltra_feedback_service/metrics.py`. §19.2 advances a household on the strength of its feedback, so the ladder was being climbed on evidence nothing counted |

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
| `services/cloud-connector` | nothing — see §2.3 |

`contracts/openapi` and `contracts/examples` are no longer on this list; they
hold their artifacts.

Each remaining directory now carries a README naming where its content actually
lives, and `tests/contract/test_layout_divergence.py` fails the build if one of
those pointers stops resolving or if a listed directory quietly gains content.
Deleting the placeholders was the other option and would have been tidier; it
would also have removed the only place a reader looking for `models/exported/`
would think to look.

---


### The console navigation has two items §4 does not list

`§4` fixes the primary navigation and its order, and the console's own test
asserts it exactly — "an item missing here is an item a user cannot reach; an
extra one is an invented product surface."

**Scenes** and **Goals** were added on 2026-08-22 at the owner's instruction,
after looking at the earlier SYLTRA product where both were first-class
sections. They sit between Devices and Automations, in the order a household
thinks in: what am I about to do, what must stay true, and only then what fires
by itself.

This is a change to the specified information architecture, not an oversight,
and it is recorded here rather than left for a reader of §4 to discover in a
test file. If the UI spec is revised, this is the paragraph it should absorb.

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
| Awaiting your decision | 2 | you |
| Needs a person | 3 | scheduling |
| Known engineering gaps | 0 | — |
| Structural divergence | 3 groups | explained in place, not resolved |

Nothing in §1 through §5 is a *critical blocker* in the sense of §32 item 18:
the platform runs, its safety guarantees hold, and its tests pass. §1.1 and §1.2
are the two that should worry you, and both close the same way — by putting it
in a real house with the dispatch switch off.
