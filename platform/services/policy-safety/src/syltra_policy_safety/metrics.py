"""Policy and Safety metrics (spec §29).

The counter that matters most here is `DECISIONS` broken down by outcome. In a
pilot week the platform runs with dispatch disabled, so the only evidence of
what it *would* have done is what policy decided — a week of DENY is a very
different pilot from a week of ALLOW, and the difference is invisible without
this.

`safety_class` is a label because a refusal on a comfort action and a refusal on
a life-safety one are not the same event, and averaging them hides the one worth
reading.
"""

from prometheus_client import Counter, Gauge, Histogram

DECISIONS = Counter(
    "syltra_policy_decisions_total",
    "policy decisions, by outcome and safety class",
    ["outcome", "safety_class"],
)
DECISION_LATENCY = Histogram(
    "syltra_policy_decision_latency_seconds",
    "time to evaluate the rule chain",
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25),
)
DECIDING_RULE = Counter(
    "syltra_policy_deciding_rule_total",
    "which rule settled the decision",
    ["rule", "outcome"],
)
APPROVALS_PENDING = Gauge(
    "syltra_policy_approvals_pending",
    "decisions waiting for a person",
    ["home_id"],
)
