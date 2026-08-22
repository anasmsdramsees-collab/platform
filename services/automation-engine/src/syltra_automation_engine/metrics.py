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

SCHEDULED_FIRINGS = Counter(
    "syltra_automation_scheduled_firings_total",
    "scheduled automations that came due, and whether they ran late",
    ["late"],
)

DISPATCHES = Counter(
    "syltra_automation_dispatches_total",
    "automation actions that reached the policy gate, by outcome and whether "
    "the device confirmed the new state",
    ["outcome", "carried_out"],
)
"""The counter that would have caught the gap this dispatcher closed.

`PROPOSALS` counted rules firing and rose every day. Nothing counted what
happened next, so a graph of a healthy-looking hub was a graph of a hub that
had never turned on a light. `carried_out` is the label that matters: a
dispatch nothing read back is not a light that came on.
"""
