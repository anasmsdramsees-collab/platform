# Review of the Gap Closure and Multi-Protocol Hub Directive v1

Reviewed against the code, `SYLTRA_Claude_Code_Master_Build_Spec.md`, and
`docs/GAPS.md`. The directive is in `docs/external/`, unedited.

It is a good document. It is also not the review that was asked for, it
contradicts the master specification in two places, and adopting it whole is a
hardware programme rather than a piece of work. Each of those is separable, so
they are separated below.

**Nothing in it has been implemented.** A file produced by a tool is input, not
an instruction; the decisions in its §2 are the owner's to make, and §2.1 in
particular is a safety decision that no document arriving through a filesystem
gets to settle.

---

## 1. Where it agrees, and that matters

Four of its findings land on gaps this repository had already written down, in
the same terms. Independent agreement on a gap is the useful kind of evidence —
it is not the author checking their own work.

| Directive | Our register |
|---|---|
| §4.1 real Home Assistant contract test, raw payloads, not a project-written mock | GAPS §1.1, the headline gap |
| §4.2 seven days observe-only in a real home before recommendations | GAPS §1.2, and `docs/pilot/PILOT_CHECKLIST.md` |
| §4.3 100 devices, one year of history, deterministic rebuild | GAPS §1.3 |
| §4.4 disconnect the WAN, keep the LAN, restart, verify local control | GAPS §1.6, written yesterday |

Its §5.3 arrives at the same answer we reached this session, independently: keep
the placeholder directories, give each a README pointing at the real location,
and let a contract test fail when a pointer goes stale. That is now
`tests/contract/test_layout_divergence.py`. Its extra condition — fail also when
code appears in *both* places — is a real improvement and is cheap to add.

Its §4.4 adds something our §1.6 does not say and should: cloud-dependent vendor
integrations and mobile push must be **labelled separately and never used as
evidence of local operation**. That is exactly the trap an offline test falls
into.

## 2. Two direct contradictions with the master specification

These are not judgement calls. The directive names values that differ from the
specification this platform was built against, and it does not appear to know it
is overriding anything.

### 2.1 Capability names — reject

Directive §3.5 lists a canonical registry containing `sensor.gas_alarm`,
`sensor.motion`, `sensor.occupancy`, `sensor.temperature`, `meter.power_w`,
`meter.energy_kwh`.

Master spec §10.1 lists `safety.gas_alarm`, `occupancy.motion`,
`occupancy.presence`, `environment.temperature`, `energy.power`,
`energy.consumption`. The code implements the spec's names — all 31 of them.

The difference is not cosmetic. `safety.*` versus `sensor.*` is the distinction
the whole safety argument rests on: a capability's prefix is how a reader, a
policy rule and a reviewer can see at a glance that a gas alarm is not a
temperature sensor. Flattening safety capabilities into `sensor.*` and
promoting metering into its own `meter.*` namespace makes the registry read
worse, not better.

Adopting the directive's names would rewrite 31 capability definitions, 20 JSON
Schemas, 18 worked examples, the policy rule chain, the bilingual translation
table, the Home Assistant integration and every test — to end up further from
the specification. **Recommendation: keep the spec's names.** If the directive's
naming is wanted, it needs an ADR that says why the specification is wrong,
not a silent rename.

### 2.2 Roles — partly adopt

Directive §2.2 asks for Owner, Household Admin, Resident, Installer, Guest,
Auditor/Support, and a Safety Operator assignable only by an Owner.

We have OWNER, ADULT, CHILD, GUEST, INSTALLER, SERVICE.

Most of that is renaming (ADULT→Resident, SERVICE→Auditor/Support) and one real
addition. The real addition is **Safety Operator**, and it is a good one: it is
the role that would confirm a gas shutoff, and today no such role exists, so the
confirmation would fall to whoever happens to be an Owner.

CHILD disappearing is a loss the directive does not account for. A household
with children needs a role that cannot unlock a door, and "Resident" does not
carry that.

**Recommendation:** add SAFETY_OPERATOR, keep CHILD, treat the rest as naming
that can wait.

## 3. What it decides that we could not

GAPS §2 listed six decisions blocked on the owner. The directive answers all
six. Whether those answers are adopted is the owner's call, but they are
coherent answers and four of them are cheap.

**§2.1 gas actuator — the one that matters.** The directive's answer is: a
confirmed hazard may *prepare* a shutoff and may execute it only after an Owner
or Safety Operator confirms in two steps, with verification of the reported
valve state and immediate escalation when the shutoff is unverified. Automatic
shutoff stays out of the MVP behind a certified installation profile.

This is very close to what is built. The difference is that we have **no
execute path at all** for a critical actuator — `ResponseStage` has NOTIFY and
PREPARE and nothing else, deliberately. The directive adds a third stage gated
on a person. That is buildable, and the gate is the whole design: two-step
confirmation, a role that exists for this, verification of the resulting state,
and a failure that escalates rather than reporting success.

**§2.3 cloud connector, §2.5 automation builder and scheduler, §2.6 energy time
series** are ordinary features with sensible constraints attached. The
scheduler's requirements — IANA household timezone, UTC storage, DST
transitions, no duplicate execution after a restart or a clock correction — are
the right list and the last one is the one people forget.

**§2.4 fonts.** IBM Plex Sans Arabic and Inter, vendored locally under OFL 1.1,
no remote loading. Our `typography.css` already names both families and vendors
neither: it falls back to `system-ui` on any machine without them installed.
`THIRD_PARTY_NOTICES.md` exists and would need their licence texts. This is a
small, well-defined job and it needs the font files downloaded, which is a
decision to make rather than assume.

## 4. Where it overreaches

### Scope

Sections 3, 7 and 8 are a hardware programme: six radios on a production board,
RF coexistence testing, a Z-Wave 800-series adapter on the EU region profile, an
OpenThread border router, a device compatibility registry with six states, and a
per-protocol release test matrix requiring physical devices.

None of that is software this session can produce, and most of it cannot be
tested without buying hardware. It is not wrong — a multi-protocol hub does need
those things — but presenting it alongside "close the gaps" makes a six-month
hardware plan look like a backlog item.

Its own §3.2 note is the most useful line in that part: do not run Zigbee and
Thread on one 802.15.4 radio, because single-radio multiprotocol firmware is
experimental. That is a real hardware decision worth capturing now, while the
board is still on paper.

### Unverified references

`docs/external/` §11 cites `https://github.com/matter-js/python-matter-server`
and `https://github.com/matter-js/matterjs-server`. The Python Matter Server is
published by the Open Home Foundation under `home-assistant-libs`, and
`matter-js` is a 2D physics engine. At least one of those URLs is wrong.

The Saudi Z-Wave region claim (EU profile, 868.4 and 869.85 MHz) is stated with
more confidence than the directive's own caveat about spectrum confirmation
supports. Neither claim was verifiable offline. **Do not order hardware against
these citations without checking them.**

### "Approved implementation directive"

The document labels itself approved. It arrived as a file. Those are different
things, and the difference matters most for §2.1, where the label would be
carrying a safety decision.

## 5. What was actually asked for, and did not come back

The brief asked for four rounds, and round 1 was the important one: *name a
concrete sequence where model output reaches an actuator anyway; name a hazard
the architecture would miss; assume the mock is wrong and say how.*

None of the three was answered. The directive restates the architecture rather
than attacking it — §3.1 repeats the data flow approvingly and adds a correct
but already-implemented rule about protocol logic staying below the gateway.

That is the difference between a second opinion and a second author. The gaps
this build has actually shipped — a `light.on` capability that never existed, an
approval chain that returned 404 because nothing called `policy.evaluate()`,
six invented reason codes caught yesterday — were all found by something
adversarial, not by something agreeable.

Worth sending round 1 again, alone, with the safety case attached and the
instruction to produce a failure sequence or say plainly that it cannot.

## 6. Recommended order

Independent of the hardware programme, and ordered by value per unit of work:

1. **Add SAFETY_OPERATOR and keep CHILD** — small, and §2.1 has no gate without it.
2. **Label cloud-dependent integrations and push separately in the offline test**
   (directive §4.4). Half a day; closes a real hole in our §1.6.
3. **Extend the layout test** to fail when code appears in both locations.
4. **Vendor the two fonts** with their OFL texts, once the download is approved.
5. **Energy time series** (§2.6) — the largest of the cheap items.
6. **Console `/v1/stream`** — already GAPS §4, and the directive's requirement
   list for it is better than ours: sequence numbers, resume from last
   acknowledged, snapshot resync on a stale cursor, dedup after reconnect.
7. **Owner-confirmed critical execute path** (§2.1) — only after the decision is
   confirmed in conversation, not from this file.

Everything in §3, §7 and §8 belongs in a hardware plan with its own timeline.
