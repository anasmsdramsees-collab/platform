"""Automation Engine metrics (spec §29 in spirit; automations arrived later).

`SKIPPED` by reason is the useful one. "Why didn't my automation run?" is the
question this component generates, and a counter per reason answers it across a
week without reading a log.
"""

from prometheus_client import Counter, Gauge

PROPOSALS = Counter(
    "syltra_automation_proposals_total",
    "actions proposed by a user-authored automation",
    ["home_id"],
)
SKIPPED = Counter(
    "syltra_automation_skipped_total",
    "automations evaluated and not fired, by reason",
    ["reason"],
)
REGISTERED = Gauge(
    "syltra_automation_registered",
    "automations stored, by enabled state",
    ["home_id", "enabled"],
)
