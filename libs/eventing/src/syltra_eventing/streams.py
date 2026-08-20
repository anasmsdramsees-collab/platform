"""JetStream stream policy (spec §12).

Raw high-frequency data keeps shorter retention than derived events, and every
stream's retention is overridable through configuration (per-privacy-class
tuning happens by adjusting the streams that carry each class). Duplicate
delivery is absorbed by JetStream's dedup window keyed on the ``Nats-Msg-Id``
header, which publishers set to the immutable ``event_id`` (supports safety
invariant 10: duplicate events do not produce duplicate actions).
"""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import timedelta
from typing import Final

from nats.js import JetStreamContext
from nats.js.api import RetentionPolicy, StreamConfig
from nats.js.errors import NotFoundError

_DEDUP_WINDOW_SECONDS: Final[int] = 120


@dataclass(frozen=True)
class StreamSpec:
    name: str
    subjects: tuple[str, ...]
    max_age: timedelta
    description: str


STREAM_SPECS: Final[tuple[StreamSpec, ...]] = (
    StreamSpec(
        name="SYLTRA_RAW",
        subjects=("syltra.raw.>",),
        max_age=timedelta(hours=24),
        description="Raw device events (high frequency, short retention)",
    ),
    StreamSpec(
        name="SYLTRA_NORMALIZED",
        subjects=("syltra.normalized.>",),
        max_age=timedelta(days=7),
        description="Normalized capability events (twin/context/AI input)",
    ),
    StreamSpec(
        name="SYLTRA_DERIVED",
        subjects=(
            "syltra.twin.>",
            "syltra.context.>",
            "syltra.ai.>",
            "syltra.risk.>",
            "syltra.policy.>",
            "syltra.action.>",
            "syltra.feedback.>",
        ),
        max_age=timedelta(days=30),
        description="Derived platform events (longer retention for audit/replay)",
    ),
    StreamSpec(
        name="SYLTRA_SYSTEM",
        subjects=("syltra.system.>",),
        max_age=timedelta(days=3),
        description="Hub and service health events",
    ),
    StreamSpec(
        name="SYLTRA_DEADLETTER",
        subjects=("syltra.deadletter.>",),
        max_age=timedelta(days=7),
        description="Poison or permanently failing events with reason codes",
    ),
)


async def ensure_streams(
    js: JetStreamContext,
    max_age_overrides: Mapping[str, timedelta] | None = None,
) -> list[str]:
    """Create or update the SYLTRA streams; returns the stream names touched.

    ``max_age_overrides`` maps stream name to retention, allowing deployments
    to tune retention (e.g. stricter privacy classes → shorter retention)
    without code changes.
    """
    touched: list[str] = []
    overrides = dict(max_age_overrides or {})
    for spec in STREAM_SPECS:
        max_age = overrides.get(spec.name, spec.max_age)
        config = StreamConfig(
            name=spec.name,
            description=spec.description,
            subjects=list(spec.subjects),
            retention=RetentionPolicy.LIMITS,
            max_age=max_age.total_seconds(),
            duplicate_window=float(_DEDUP_WINDOW_SECONDS),
        )
        try:
            await js.update_stream(config)
        except NotFoundError:
            await js.add_stream(config)
        touched.append(spec.name)
    return touched


async def purge_streams(js: JetStreamContext) -> list[str]:
    """Purge all SYLTRA streams (demo reset only — never selective user data)."""
    purged: list[str] = []
    for spec in STREAM_SPECS:
        try:
            await js.purge_stream(spec.name)
        except NotFoundError:
            continue
        purged.append(spec.name)
    return purged
