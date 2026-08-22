# Consent model

Spec §26 requires per-feature consent. The model here is deliberately narrow:
consent is granted per *capability of the platform*, not as a single "accept
everything", and the absence of consent is a denial rather than a default-on.

## Consent is checked, not assumed

`HomePolicy.consented_policies` is a set of policy names a household has agreed
to. `rule_consent_required` runs early in the policy chain and denies anything
whose `required_policy` is not in that set:

```python
if recommendation.required_policy not in policy.consented_policies:
    return DENY, ["CONSENT_NOT_GRANTED"]
```

A new feature therefore arrives switched **off**. Adding a policy name to the
code does not enable it for any home; a household has to grant it.

## The consent surface

| Policy | Covers | Default |
|---|---|---|
| `COMFORT_AUTOMATION` | Lights, climate, covers, switches | Granted at commissioning |
| `SECURITY_AUTOMATION` | Locks, garage, camera recording | **Not granted** |
| `ENERGY_INSIGHTS` | Anomaly detection and reporting | **Not granted** |
| `CLOUD_SYNC` | Any export off the hub | **Not granted, and not implemented** |

## Consent is not the only gate

Granting `COMFORT_AUTOMATION` does not mean the platform will act unattended. It
still has to pass:

- the **learning ladder** (spec §19.2) — a home starts in `OBSERVE` and is
  advanced one rung at a time by a person;
- the **confidence thresholds** and **approval requirements** in policy;
- the **capability confirmation level** — locks always need explicit approval,
  whatever consent says.

So consent answers "may the platform consider this at all?", and the rest of the
policy chain answers "should it act now?".

## Withdrawal

Three levels, all immediate:

| Action | Effect | Where |
|---|---|---|
| Remove a policy from `consented_policies` | That whole feature stops | Policy service |
| `NEVER_REPEAT` on a recommendation | That recommendation type stops permanently for the home | Feedback → policy suppression |
| Set learning mode to `DISABLED` | The platform stops proposing anything | Adaptive engine |

`NEVER_REPEAT` is durable by design: a later `ACCEPT` on the same type does not
quietly revive it (`test_never_repeat_suppresses_the_type_permanently`).

## What consent can never authorize

No consent setting grants authority over life-safety actuators. `ACT_SAFETY`
belongs to no role, and gas valves, breakers and sirens are commanded only by
deterministic safety rules (safety invariants 6, 13, 18). A household cannot
opt *into* letting the learning layer operate them, because that path does not
exist.

## Recording consent changes

Consent changes are audited with actor and reason like any other sensitive
change (spec §25.5). A household can see, in the console's audit view, who
changed what and when.
