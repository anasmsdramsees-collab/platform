"""Constants for the SYLTRA Edge integration (spec §27).

The domain is unique to SYLTRA and does not shadow any built-in integration
(spec §27: use a unique integration domain, avoid overriding built-ins).
"""

from datetime import timedelta
from typing import Final

DOMAIN: Final = "syltra_edge"
"""Unique to SYLTRA. Home Assistant Core is never modified (ADR-001)."""

CONF_EDGE_URL: Final = "edge_url"
CONF_VERIFY_TLS: Final = "verify_tls"

DEFAULT_EDGE_URL: Final = "http://localhost:8081"
DEFAULT_SCAN_INTERVAL: Final = timedelta(seconds=30)

HEALTH_PATH: Final = "/health/ready"
LIVE_PATH: Final = "/health/live"
METRICS_PATH: Final = "/metrics"

ATTR_CONNECTED: Final = "connected"
ATTR_LAST_ERROR: Final = "last_error"

SERVICE_REFRESH_HEALTH: Final = "refresh_health"
"""The only service registered. Deliberately SYLTRA-specific: it does not
duplicate any standard entity service (spec §27)."""

# Never logged, never included in diagnostics.
REDACTED_KEYS: Final = frozenset(
    {"token", "access_token", "password", "api_key", "authorization", "secret"}
)
