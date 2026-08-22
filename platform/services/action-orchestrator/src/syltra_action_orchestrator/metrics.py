"""Action Orchestrator metrics (spec §29).

Three of §29's required metrics live here, and they answer the questions a pilot
asks in order: did anything run, did it work, and did a person have to step in.

`REFUSALS` carries the reason code, which is what makes an observe-only week
readable: `DISPATCH_DISABLED_OBSERVE_ONLY` counted separately from
`MANUAL_OVERRIDE_DETECTED` is the difference between "the hub was watching" and
"the hub tried and a person stopped it".
"""

from prometheus_client import Counter, Gauge, Histogram

ACTIONS = Counter(
    "syltra_action_results_total",
    "action outcomes, by status and safety class",
    ["status", "safety_class"],
)
REFUSALS = Counter(
    "syltra_action_refusals_total",
    "actions refused before dispatch, by reason",
    ["reason_code", "safety_class"],
)
MANUAL_OVERRIDES = Counter(
    "syltra_action_manual_overrides_total",
    "pending actions cancelled because a person took control",
    ["home_id"],
)
DISPATCH_LATENCY = Histogram(
    "syltra_action_dispatch_latency_seconds",
    "request-to-verified latency",
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)
ATTEMPTS = Histogram(
    "syltra_action_attempts",
    "dispatch attempts per action",
    buckets=(1, 2, 3, 4, 5),
)
DISPATCH_ENABLED = Gauge(
    "syltra_action_dispatch_enabled",
    "1 when this hub may command a device, 0 when it is observing only",
)
