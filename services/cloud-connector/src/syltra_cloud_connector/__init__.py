"""SYLTRA Cloud Connector.

Disabled by default. Exports only fields a household named, to destinations a
household consented to, redacted, through a bounded queue that no control path
waits on. See `connector.py` for why each of those is a separate gate.
"""

from syltra_cloud_connector.connector import (
    DEFAULT_QUEUE_LIMIT,
    CloudConnector,
    Consent,
    Destination,
    ExportRefused,
)

__all__ = [
    "DEFAULT_QUEUE_LIMIT",
    "CloudConnector",
    "Consent",
    "Destination",
    "ExportRefused",
]
