"""Energy over time, without inventing any of it (spec §17.11, §27 criterion 9).

The Energy screen showed current power and nothing else — no trend, no
comparison, no cost — because the platform recorded readings and kept no
aggregation. This is the aggregation, and most of its design is about the one
rule that makes it trustworthy.

## §17.11: never estimate a measurement

A meter that reported nothing between 02:00 and 05:00 did not consume zero
watts. It consumed an unknown amount. Every other energy dashboard fills that
gap — with a flat line, with the last value, with an interpolation — and the
household reads a number nobody measured.

So a bucket with no samples is **absent**, not zero. `EnergyBucket` cannot be
constructed with a sample count of zero, and `coverage` reports what fraction of
the expected samples actually arrived. A chart drawn from this data has holes in
it, and the holes are the honest part.

## Why mean, and what it is a mean of

`watts` is the arithmetic mean of the samples in the bucket, which is the right
average for converting to energy only when samples are evenly spaced. They are
not always. So the bucket also carries `samples` and `coverage`, and anything
deriving kilowatt-hours from a low-coverage bucket is deriving them from a
guess — which is why this module offers no kWh field at all. Energy in kWh needs
a meter that reports cumulative energy, and `energy.consumption` is the
capability for that.

## Cost

Absent, deliberately. A tariff has effective dates, tiers, and a currency, and a
cost figure computed from the wrong one of those is worse than no cost figure.
When a tariff exists it belongs beside the reading, labelled as calculated
rather than measured.
"""

import logging
from bisect import bisect_left
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)

#: How much history one household keeps in process. A pilot hub reads a handful
#: of meters every few seconds; this is roughly a fortnight of that, and the
#: durable copy lives in `device_events` for a deployment with a database.
MAX_SAMPLES_PER_SERIES = 200_000


class Resolution(StrEnum):
    """Bucket sizes a household actually asks for."""

    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"

    @property
    def delta(self) -> timedelta:
        return {
            Resolution.MINUTE: timedelta(minutes=1),
            Resolution.HOUR: timedelta(hours=1),
            Resolution.DAY: timedelta(days=1),
        }[self]

    def floor(self, moment: datetime) -> datetime:
        if self is Resolution.MINUTE:
            return moment.replace(second=0, microsecond=0)
        if self is Resolution.HOUR:
            return moment.replace(minute=0, second=0, microsecond=0)
        return moment.replace(hour=0, minute=0, second=0, microsecond=0)


@dataclass(frozen=True)
class EnergySample:
    at: datetime
    watts: float
    device_id: str | None = None
    room_id: str | None = None


@dataclass(frozen=True)
class EnergyBucket:
    """One interval, described only by what was measured in it."""

    start: datetime
    resolution: Resolution
    watts: float
    minimum: float
    maximum: float
    samples: int
    expected_samples: int

    def __post_init__(self) -> None:
        # A bucket with no samples must not exist. Its absence from the series
        # is the statement "nothing was measured here", and a zero-sample bucket
        # carrying watts=0.0 would say something different and untrue.
        if self.samples <= 0:
            msg = "an energy bucket with no samples is a gap, not a measurement"
            raise ValueError(msg)

    @property
    def coverage(self) -> float:
        """Fraction of the expected samples that arrived, capped at 1.0."""
        if self.expected_samples <= 0:
            return 1.0
        return min(1.0, self.samples / self.expected_samples)

    def as_view(self) -> dict[str, Any]:
        return {
            "start": self.start.isoformat(),
            "watts": round(self.watts, 2),
            "minimum": round(self.minimum, 2),
            "maximum": round(self.maximum, 2),
            "samples": self.samples,
            "coverage": round(self.coverage, 3),
        }


@dataclass(frozen=True)
class EnergySeries:
    """A run of buckets, and an explicit account of what is missing from it."""

    home_id: str
    resolution: Resolution
    start: datetime
    end: datetime
    buckets: tuple[EnergyBucket, ...]
    missing: tuple[datetime, ...]

    @property
    def covered(self) -> float:
        total = len(self.buckets) + len(self.missing)
        return 1.0 if total == 0 else len(self.buckets) / total

    def as_view(self) -> dict[str, Any]:
        return {
            "home_id": self.home_id,
            "resolution": self.resolution.value,
            "from": self.start.isoformat(),
            "to": self.end.isoformat(),
            "buckets": [bucket.as_view() for bucket in self.buckets],
            # Named rather than implied by absence, so a chart can draw the gap
            # instead of joining across it — a line through a hole is a claim
            # about what happened in the hole.
            "missing": [moment.isoformat() for moment in self.missing],
            "coverage": round(self.covered, 3),
            # The screen says this out loud. Spec §17.11 forbids estimating a
            # measurement, and a reader deserves to know that is why the line
            # stops rather than assuming the hub was off.
            "estimated": False,
        }


class EnergyHistory:
    """Readings kept in time order, per home and per device."""

    def __init__(self, max_samples: int = MAX_SAMPLES_PER_SERIES) -> None:
        self._samples: dict[str, list[EnergySample]] = defaultdict(list)
        self._max = max_samples

    def record(
        self,
        home_id: str,
        watts: float,
        at: datetime,
        device_id: str | None = None,
        room_id: str | None = None,
    ) -> None:
        """Keep one measured reading.

        Out-of-order arrivals are inserted in place rather than appended: a
        device that reconnects and replays its buffer would otherwise produce a
        series that jumps backwards, and every bucket after it would be wrong.
        """
        series = self._samples[home_id]
        sample = EnergySample(at=at, watts=float(watts), device_id=device_id, room_id=room_id)
        if series and at < series[-1].at:
            series.insert(bisect_left([s.at for s in series], at), sample)
        else:
            series.append(sample)
        if len(series) > self._max:
            del series[: len(series) - self._max]

    def earliest(self, home_id: str) -> datetime | None:
        series = self._samples.get(home_id)
        return series[0].at if series else None

    def series(
        self,
        home_id: str,
        resolution: Resolution,
        start: datetime,
        end: datetime,
        device_id: str | None = None,
    ) -> EnergySeries:
        """Aggregate what was measured between `start` and `end`."""
        samples = [
            s
            for s in self._samples.get(home_id, [])
            if start <= s.at < end and (device_id is None or s.device_id == device_id)
        ]

        grouped: dict[datetime, list[float]] = defaultdict(list)
        for sample in samples:
            grouped[resolution.floor(sample.at)].append(sample.watts)

        # How many samples a full bucket would hold, estimated from the median
        # gap between readings actually seen. Estimating the *expected count* is
        # fine; estimating a reading is not. The difference matters: one shapes
        # a confidence figure, the other invents a measurement.
        expected = _expected_samples(samples, resolution)

        buckets = tuple(
            EnergyBucket(
                start=moment,
                resolution=resolution,
                watts=sum(values) / len(values),
                minimum=min(values),
                maximum=max(values),
                samples=len(values),
                expected_samples=expected,
            )
            for moment, values in sorted(grouped.items())
        )

        missing = []
        cursor = resolution.floor(start)
        while cursor < end:
            if cursor not in grouped:
                missing.append(cursor)
            cursor += resolution.delta

        return EnergySeries(
            home_id=home_id,
            resolution=resolution,
            start=start,
            end=end,
            buckets=buckets,
            missing=tuple(missing),
        )


def _expected_samples(samples: list[EnergySample], resolution: Resolution) -> int:
    """Samples a full bucket would hold, from the observed reporting interval."""
    if len(samples) < 2:
        return 1
    gaps = sorted(
        (b.at - a.at).total_seconds()
        for a, b in zip(samples, samples[1:], strict=False)
        if (b.at - a.at).total_seconds() > 0
    )
    if not gaps:
        return 1
    median = gaps[len(gaps) // 2]
    return max(1, int(resolution.delta.total_seconds() // median))


def now_utc() -> datetime:
    return datetime.now(tz=UTC)
