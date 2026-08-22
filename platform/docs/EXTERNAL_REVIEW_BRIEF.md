# Brief for an outside reviewer

This exists to be pasted into another assistant — ChatGPT or any other — so the
platform gets read by something that did not build it. `docs/GAPS.md` §3 says
three things need a person who is not the author; a second model is not a person,
but it is not the author either, and that is most of the value.

Everything below is written to be copied. Nothing in it depends on the reviewer
having repository access.

---

## How to run it

There are four rounds. Do them in order — each one's answer changes what is
worth asking next. Paste one round, bring the answer back, and it gets acted on
before the next goes out.

Attach with round 1: `docs/PLATFORM_OVERVIEW.md`, `docs/GAPS.md`.
Attach with round 2: `docs/safety/SAFETY_CASE.md`, `docs/safety/RISK_STATE_MACHINE.md`.
Attach with round 3: `docs/pilot/PILOT_CHECKLIST.md`.
Round 4 needs nothing new.

Total is about 6,000 words of attachments — inside any current context window.

---

## Round 1 — attack the safety argument

> You are reviewing a local-first smart-home platform built by someone else. Two
> documents are attached: an overview, and the author's own register of gaps.
>
> Do not summarise them and do not tell me what is good. Your job is to find
> what is wrong.
>
> The central claim is: **an ML model can never cause a physical action.** Model
> output is a recommendation; a deterministic policy chain decides; only a
> Safety Governor can confirm a hazard, and only from a certified alarm reading.
>
> Give me the strongest case that this claim is false or incomplete as
> described. Specifically:
>
> 1. Name a concrete sequence of events where model output reaches an actuator
>    anyway. Be specific about the step where the barrier fails.
> 2. Name a hazard the described architecture would miss entirely.
> 3. The author says the Home Assistant boundary has only ever been tested
>    against a mock they wrote themselves. Assuming that mock is wrong in some
>    way, what is the most damaging way it could be wrong?
>
> If you think the claim holds, say so and explain what would have to be true
> for it to fail — do not manufacture an objection to be useful.

## Round 2 — the safety case as a document

> Attached is the safety case and the risk state machine for the platform you
> reviewed. Eighteen safety invariants are claimed to be enforced structurally
> rather than by convention.
>
> Read them as a certification reviewer would.
>
> 1. Which invariants are stated in a way that cannot actually be tested? Quote
>    each one and say what would have to change for it to be testable.
> 2. Which are enforced only by the code agreeing to enforce them — that is,
>    which would a careless future change silently break?
> 3. The seven risk states are NORMAL, WATCH, PRE_ALERT, CONFIRMED,
>    ACTION_IN_PROGRESS, RECOVERY, CLOSED. Find a real household situation the
>    machine handles badly, or a transition it is missing.

## Round 3 — the six open decisions

> `docs/GAPS.md` §2 lists six product decisions the author refused to make on
> the owner's behalf. The pilot checklist is attached.
>
> The one that matters most: **may a confirmed hazard operate an actuator?**
> Today the answer is no — a confirmed gas alarm notifies and prepares, and a
> human closes the valve. The alternative is letting the Safety Governor act
> alone on a certified alarm.
>
> Argue both sides properly, then recommend one. Address at least:
>
> - what liability changes when the machine turns the valve;
> - what happens on a false positive from a certified detector, and how often
>   that actually is;
> - whether "notify and prepare" is a real safety posture or a way of avoiding
>   the decision;
> - what a regulator in a Gulf residential market would expect.
>
> Then, briefly, the other five decisions in §2.

## Round 4 — what the register misses

> You have now read the overview, the gap register, the safety case, the risk
> machine and the pilot checklist.
>
> The author wrote the gap register themselves, which means it has the blind
> spots of the person who built the thing.
>
> What is missing from it? Name gaps that a builder would not think to write
> down about their own work. Be concrete — "consider security" is useless;
> "nothing in these documents says what happens when two people in the house
> give contradictory instructions within the same minute" is useful.
>
> Rank what you find by how expensive it gets to fix later.

---

## What happens to the answers

Bring them back and they get treated as claims, not conclusions. Each one is
checked against the code before anything changes — an outside reviewer working
from documents can only see what the documents say, and this build has already
turned up several places where the documents and the code disagreed.

A finding that survives that check becomes an entry in `docs/GAPS.md` with the
reviewer named as its source, or a fix with a test.

## What this cannot do

There is no live connection between the two assistants. Nothing here is
automated: a person carries each round across, and that person is the one who
decides which findings are worth acting on. That is not a limitation worth
engineering away — a second opinion that nobody reads is not a second opinion.
