"""Feedback metrics (spec §29 in spirit, not in its list of fourteen).

The other six services carry instrumentation and this one did not, which left a
blind spot exactly where a pilot needs sight. The learning ladder in §19.2 only
moves a household forward on evidence that its recommendations are welcome, and
that evidence is feedback. Without these counters the question "should this home
advance from RECOMMEND to AUTHORIZED_AUTOMATION?" has to be answered by reading
the audit trail by hand.

`suppressed` is the one to watch. A type the household refused outright is a
standing instruction, and a rising count is the platform being told to stop —
which is a healthier signal than silence, and worth seeing on a dashboard rather
than discovering in a complaint.
"""

from prometheus_client import Counter, Gauge

RESPONSES = Counter(
    "syltra_feedback_responses_total",
    "responses recorded, by kind and who gave them",
    ["kind", "source"],
)
SUPPRESSED_TYPES = Gauge(
    "syltra_feedback_suppressed_types",
    "recommendation types this household has refused outright",
    ["home_id"],
)
TYPES_NEEDING_SUSPENSION = Gauge(
    "syltra_feedback_types_needing_suspension",
    "recommendation types whose standing has fallen far enough to withdraw (§19.4)",
    ["home_id"],
)
ACCEPTANCE_RATE = Gauge(
    "syltra_feedback_acceptance_rate",
    "share of responses that accepted, per recommendation type",
    ["home_id", "recommendation_type"],
)
