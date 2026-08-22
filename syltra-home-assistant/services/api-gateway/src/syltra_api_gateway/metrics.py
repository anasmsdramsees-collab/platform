"""API Gateway metrics (spec §29)."""

from prometheus_client import Counter, Gauge, Histogram

REQUESTS = Counter(
    "syltra_api_requests_total", "API requests", ["route", "status"]
)
REQUEST_LATENCY = Histogram(
    "syltra_api_request_latency_seconds", "API request latency", ["route"]
)
APPROVALS = Counter(
    "syltra_api_approvals_total", "approval decisions taken by users", ["outcome"]
)
FEEDBACK = Counter("syltra_api_feedback_total", "feedback submitted", ["kind"])
STREAM_CONNECTIONS = Gauge(
    "syltra_api_stream_connections", "open WebSocket stream connections"
)
AUTH_FAILURES = Counter(
    "syltra_api_auth_failures_total", "authentication and authorization failures", ["code"]
)
