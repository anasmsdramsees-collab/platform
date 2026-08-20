"""Risk Engine metrics (spec §29).

`ACTIVE_CASES` is labelled by state as well as category, because the single
number §29 asks for would merge an advisory watch with a confirmed hazard — and
those are the two things this platform exists to keep apart.
"""

from prometheus_client import Counter, Gauge

ACTIVE_CASES = Gauge(
    "syltra_risk_active_cases",
    "open risk cases, by state and category",
    ["home_id", "state", "category"],
)
CASE_CHANGES = Counter(
    "syltra_risk_case_changes_total",
    "risk case transitions",
    ["kind", "category"],
)
CONFIRMATIONS = Counter(
    "syltra_risk_confirmations_total",
    "hazards confirmed by a deterministic rule",
    ["category", "rule"],
)
CONFIRMATION_REFUSALS = Counter(
    "syltra_risk_confirmation_refusals_total",
    "confirmations the governor declined, by reason",
    ["reason"],
)
