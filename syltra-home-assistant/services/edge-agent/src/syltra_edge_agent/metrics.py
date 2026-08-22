"""Prometheus metrics for the Edge Agent (spec §29)."""

from prometheus_client import Counter, Gauge, Histogram

EVENTS_RECEIVED = Counter(
    "syltra_edge_events_received_total", "state_changed events received from Home Assistant"
)
EVENTS_PUBLISHED = Counter(
    "syltra_edge_events_published_total", "events published to JetStream", ["stream"]
)
EVENTS_INVALID = Counter(
    "syltra_edge_events_invalid_total", "structurally invalid events routed to dead-letter"
)
EVENTS_DUPLICATE = Counter(
    "syltra_edge_events_duplicate_total", "duplicate events suppressed"
)
EVENTS_OUT_OF_ORDER = Counter(
    "syltra_edge_events_out_of_order_total", "out-of-order events flagged"
)
EVENTS_UNMAPPED = Counter(
    "syltra_edge_events_unmapped_total", "events for entities outside the capability model"
)
RECONNECTS = Counter(
    "syltra_edge_reconnects_total", "reconnection attempts toward Home Assistant"
)
CONNECTED = Gauge(
    "syltra_edge_connected", "1 when authenticated to Home Assistant, else 0"
)
PUBLISH_LATENCY = Histogram(
    "syltra_edge_publish_latency_seconds",
    "receive-to-publish latency for normalized events",
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)
