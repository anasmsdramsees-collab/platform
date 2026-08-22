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

# The driver's own vital signs. A safety loop that stopped is invisible without
# these: every other metric here simply stops changing, which looks identical to
# a quiet house.
DRIVER_PASSES = Counter(
    "syltra_risk_driver_passes_total",
    "completed evaluation passes over every known home",
)
DRIVER_FAILURES = Counter(
    "syltra_risk_driver_failures_total",
    "homes whose evaluation raised during a pass",
    ["home_id"],
)
ISOLATIONS = Counter(
    "syltra_risk_isolations_total",
    "supplies cut by a confirmed hazard, and whether the device confirmed it",
    ["capability", "verified"],
)
