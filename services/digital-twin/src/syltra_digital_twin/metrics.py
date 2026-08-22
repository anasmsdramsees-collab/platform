"""Digital Twin metrics (spec §29)."""

from prometheus_client import Counter, Gauge, Histogram

EVENTS_CONSUMED = Counter(
    "syltra_twin_events_consumed_total", "normalized events consumed from JetStream"
)
EVENTS_APPLIED = Counter(
    "syltra_twin_events_applied_total", "events that changed observable twin state"
)
EVENTS_INVALID = Counter(
    "syltra_twin_events_invalid_total", "events rejected at the consumer boundary"
)
EVENTS_DUPLICATE = Counter(
    "syltra_twin_events_duplicate_total", "already-seen events skipped"
)
DATABASE_LATENCY = Histogram(
    "syltra_twin_database_latency_seconds",
    "time spent in the database on one persistence call",
    ["operation"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)
STATE_UPDATE_LATENCY = Histogram(
    "syltra_twin_state_update_latency_seconds",
    "consume-to-persisted latency for a state update",
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
)
TRACKED_DEVICES = Gauge(
    "syltra_twin_tracked_devices", "devices currently held in the twin", ["home_id"]
)
STALE_CAPABILITIES = Gauge(
    "syltra_twin_stale_capabilities", "capability states past their freshness window",
    ["home_id"],
)
UNKNOWN_CAPABILITIES = Gauge(
    "syltra_twin_unknown_capabilities", "capability states never observed", ["home_id"]
)
CONSUMER_CONNECTED = Gauge(
    "syltra_twin_consumer_connected", "1 when subscribed to JetStream, else 0"
)
