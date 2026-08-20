# Pilot checklist

Before a SYLTRA hub goes into an occupied home.

Spec §0 rule 9 is absolute: **never deploy to production, connect to a real
occupied home, or operate real safety actuators without explicit human
approval.** This checklist is the evidence you bring to that approval
conversation — not a substitute for it.

## 1. The platform runs

- [ ] `make bootstrap` succeeds on a clean machine
- [ ] `make up` brings up every service; all report `/health/ready`
- [ ] `make test` passes (683 unit/contract)
- [ ] `make test-integration` passes (84)
- [ ] `make test-e2e` passes (13)
- [ ] `make test-safety` passes (227) — **run this last and read the output**
- [ ] `make simulate` — 21/21 scenarios
- [ ] `make lint` clean; `make security` clean
- [ ] `make coverage` ≥ 90%

## 2. Safety

- [ ] Every one of the 18 invariants in `docs/safety/SAFETY_CASE.md` maps to a
      passing test
- [ ] The safety suite passes **with the Adaptive Engine stopped**
- [ ] The safety suite passes **with the network unavailable**
- [ ] `SYLTRA_ENVIRONMENT` is set correctly — `development` blocks critical
      actuators; a pilot in an occupied home must be deliberate about this
- [ ] Certified alarm devices are installed, commissioned, and reporting fresh
      readings
- [ ] The household knows which hazards SYLTRA watches and which it does not
- [ ] **The household knows SYLTRA is not a certified life-safety system**

## 3. Learning posture

- [ ] Every home starts in `OBSERVE`
- [ ] The pilot plan says who advances the mode, and on what evidence
- [ ] `AUTHORIZED_AUTOMATION` is not planned for week one
- [ ] Model evaluation gates are configured and understood

## 4. Privacy

- [ ] `docs/privacy/DATA_INVENTORY.md` reviewed with the household
- [ ] Consent recorded per feature; unconsented features verified off
- [ ] Export tested: `export_home()` returns the household's data
- [ ] **Deletion tested**: `delete_home()` reports `complete`
- [ ] No cloud connector configured (there is none to configure)
- [ ] Diagnostic bundle reviewed — confirm no household data in it

## 5. Security

- [ ] Home Assistant long-lived token created for SYLTRA only, rotated from any
      development value
- [ ] NATS and PostgreSQL credentials unique to this hub
- [ ] `.env` present, `0600`, never committed
- [ ] Only the API Gateway reachable from the home network
- [ ] Tokens issued per person with the least role that works
- [ ] Token expiry understood — 12 hours, not indefinite

## 6. Operations

- [ ] Backup taken, and **a restore tested from it**
- [ ] Backup passphrase stored separately from the archive
- [ ] Watchdog running; alert destination configured and tested
- [ ] `make logs` produces readable structured output
- [ ] `/metrics` scraped, or at least reachable
- [ ] The runbook has been read by whoever is on call
- [ ] Escalation contact agreed with the household

## 7. The household

- [ ] Console reachable, in their language
- [ ] Someone has been shown: approve, reject, never-repeat, and how to see why
- [ ] They know manual control always wins
- [ ] They know how to reach a person
- [ ] They know how to stop the platform entirely

## 8. Known limitations, stated plainly

Tell the household these, in words, before the hub goes in:

- SYLTRA is **not** a certified fire, gas or intrusion alarm. It watches
  certified detectors and can tell you what it sees; it does not replace them.
- It will not operate gas valves, breakers or sirens.
- It starts by observing and will not act automatically until they say so.
- Its data stays on the hub. There is no cloud.
- If the hub is off, their home works exactly as it did before.

## Sign-off

| Role | Name | Date |
|---|---|---|
| Engineering | | |
| Safety review | | |
| Privacy review | | |
| Household representative | | |

An unsigned checklist is not an approval.
