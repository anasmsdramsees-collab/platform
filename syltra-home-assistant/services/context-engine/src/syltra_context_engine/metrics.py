"""Context Engine metrics (spec §29)."""

from prometheus_client import Counter, Gauge

EVENTS_CONSUMED = Counter(
    "syltra_context_events_consumed_total", "normalized events consumed"
)
EVENTS_INVALID = Counter(
    "syltra_context_events_invalid_total", "events rejected at the consumer boundary"
)
CONTEXT_CHANGES = Counter(
    "syltra_context_changes_total",
    "context lifecycle transitions published",
    ["context_type", "kind"],
)
ACTIVE_CONTEXTS = Gauge(
    "syltra_context_active", "currently active contexts", ["home_id"]
)
MEAN_CONFIDENCE = Gauge(
    "syltra_context_mean_confidence", "mean confidence of active contexts", ["home_id"]
)
CONSUMER_CONNECTED = Gauge(
    "syltra_context_consumer_connected", "1 when subscribed to JetStream, else 0"
)
