"""Synthetic test data factories for SYLTRA.

Spec §26 requires synthetic data in development and automated tests — no real
household data ever enters this repository. Every helper here produces
fabricated identifiers and plausible-but-invented readings.
"""

from syltra_testing.factories import BASE_TIME, make_envelope, make_sequence
from syltra_testing.history import (
    HISTORY_START,
    comfort_history,
    energy_history,
    routine_history,
    sparse_history,
)
from syltra_testing.twin_builders import (
    EVENING,
    MIDDAY,
    build_device,
    build_home,
    build_reading,
    stale_by,
)

__all__ = [
    "BASE_TIME",
    "HISTORY_START",
    "EVENING",
    "MIDDAY",
    "build_device",
    "build_home",
    "build_reading",
    "comfort_history",
    "energy_history",
    "make_envelope",
    "make_sequence",
    "routine_history",
    "sparse_history",
    "stale_by",
]
