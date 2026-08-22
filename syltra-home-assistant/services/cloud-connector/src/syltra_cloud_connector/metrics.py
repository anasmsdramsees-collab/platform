"""Cloud connector metrics (spec §29: cloud connector status).

The last of §29's fourteen without a source, and it had none for the honest
reason that the component did not exist. `ENABLED` is the one a dashboard should
lead with: a household is promised that local control never depends on the
cloud, and the simplest evidence for that promise is a gauge reading zero.
"""

from prometheus_client import Counter, Gauge

ENABLED = Gauge(
    "syltra_cloud_connector_enabled",
    "1 when the connector is enabled for a home, else 0",
    ["home_id"],
)
QUEUE_DEPTH = Gauge(
    "syltra_cloud_connector_queue_depth",
    "records waiting to be delivered",
    ["home_id", "destination"],
)
REFUSALS = Counter(
    "syltra_cloud_connector_refusals_total",
    "records the connector declined to export, by reason",
    ["reason_code"],
)
DROPPED = Counter(
    "syltra_cloud_connector_dropped_total",
    "records dropped because the queue was full",
    ["home_id", "destination"],
)
DELIVERED = Counter(
    "syltra_cloud_connector_delivered_total",
    "records delivered to a destination",
    ["home_id", "destination"],
)
