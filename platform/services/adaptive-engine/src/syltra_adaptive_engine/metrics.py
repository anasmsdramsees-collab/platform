"""Adaptive Engine metrics (spec §29)."""

from prometheus_client import Counter, Gauge, Histogram

EVENTS_CONSUMED = Counter(
    "syltra_adaptive_events_consumed_total", "normalized events consumed"
)
EVENTS_INVALID = Counter(
    "syltra_adaptive_events_invalid_total", "events rejected at the consumer boundary"
)
HISTORY_SIZE = Gauge(
    "syltra_adaptive_history_events", "events retained for training", ["home_id"]
)
TRAINING_ATTEMPTS = Counter(
    "syltra_adaptive_training_attempts_total", "training attempts", ["model"]
)
TRAINING_REFUSALS = Counter(
    "syltra_adaptive_training_refusals_total",
    "training attempts refused for insufficient data",
    ["model", "reason"],
)
RECOMMENDATIONS_BUILT = Counter(
    "syltra_adaptive_recommendations_total",
    "recommendations produced",
    ["model", "shadow"],
)
INFERENCE_LATENCY = Histogram(
    "syltra_adaptive_inference_latency_seconds",
    "local model inference latency",
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5),
)
LEARNING_MODE = Gauge(
    "syltra_adaptive_learning_mode",
    "learning mode rank (-1 suspended, 0 disabled … 5 authorized automation)",
    ["home_id"],
)
MODEL_SUSPENSIONS = Counter(
    "syltra_adaptive_model_suspensions_total", "models withdrawn from service", ["model"]
)
CONSUMER_CONNECTED = Gauge(
    "syltra_adaptive_consumer_connected", "1 when subscribed to JetStream, else 0"
)
