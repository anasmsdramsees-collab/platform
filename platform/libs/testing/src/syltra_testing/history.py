"""Synthetic household history for model training tests (spec §26).

Generates plausible-but-invented event streams with known structure, so a test
can assert that a model found the pattern that was deliberately planted.
"""

import math
import random
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

from syltra_contracts import EventEnvelope
from syltra_testing.factories import make_envelope

HISTORY_START = datetime(2026, 6, 1, 0, 0, 0, tzinfo=UTC)


def routine_history(
    days: int = 28,
    hour: int = 18,
    minute: int = 30,
    capability: str = "light.power",
    device_id: str = "light_living",
    home_id: str = "home_001",
    start: datetime = HISTORY_START,
    noise_events: int = 20,
    seed: int = 7,
) -> list[EventEnvelope]:
    """A light switched on at the same time every evening, plus random noise.

    The planted routine is at ``hour:minute``; the noise is spread across other
    hours so a model that simply reports "the light is often on" would fail to
    single out the routine slot.
    """
    rng = random.Random(seed)  # noqa: S311  # nosec B311 - synthetic fixture
    events: list[EventEnvelope] = []
    for day in range(days):
        moment = start + timedelta(days=day, hours=hour, minutes=minute)
        events.append(
            make_envelope(
                capability=capability,
                value=True,
                unit=None,
                home_id=home_id,
                device_id=device_id,
                occurred_at=moment,
            )
        )
        events.append(
            make_envelope(
                capability=capability,
                value=False,
                unit=None,
                home_id=home_id,
                device_id=device_id,
                occurred_at=moment + timedelta(hours=4),
            )
        )
    for _ in range(noise_events):
        moment = start + timedelta(
            days=rng.randint(0, days - 1), hours=rng.randint(0, 11), minutes=rng.randint(0, 59)
        )
        events.append(
            make_envelope(
                capability=capability,
                value=True,
                unit=None,
                home_id=home_id,
                device_id=device_id,
                occurred_at=moment,
            )
        )
    return sorted(events, key=lambda e: e.occurred_at)


def comfort_history(
    days: int = 21,
    home_id: str = "home_001",
    start: datetime = HISTORY_START,
    seed: int = 11,
) -> list[EventEnvelope]:
    """Setpoint choices that depend on hour and indoor temperature.

    The planted relationship: warmer indoors and later in the day, the occupant
    chooses a lower setpoint. A working preference model should recover it.
    """
    rng = random.Random(seed)  # noqa: S311  # nosec B311 - synthetic fixture
    events: list[EventEnvelope] = []
    for day in range(days):
        for hour in (7, 13, 19, 22):
            moment = start + timedelta(days=day, hours=hour)
            indoor = 24.0 + 4.0 * math.sin(2 * math.pi * hour / 24) + rng.uniform(-0.5, 0.5)
            events.append(
                make_envelope(
                    capability="environment.temperature",
                    value=round(indoor, 2),
                    unit="C",
                    home_id=home_id,
                    device_id="climate_sensor",
                    occurred_at=moment,
                )
            )
            setpoint = 25.0 - 0.35 * (indoor - 24.0) - (1.0 if hour >= 19 else 0.0)
            events.append(
                make_envelope(
                    capability="climate.target_temperature",
                    value=round(min(max(setpoint, 16.0), 30.0), 1),
                    unit="C",
                    home_id=home_id,
                    device_id="ac_living",
                    occurred_at=moment + timedelta(minutes=2),
                )
            )
    return sorted(events, key=lambda e: e.occurred_at)


def energy_history(
    days: int = 10,
    readings_per_day: int = 24,
    baseline_watts: float = 600.0,
    home_id: str = "home_001",
    start: datetime = HISTORY_START,
    spikes: int = 0,
    spike_watts: float = 6000.0,
    seed: int = 13,
) -> list[EventEnvelope]:
    """Whole-home power around a stable baseline, optionally with spikes."""
    rng = random.Random(seed)  # noqa: S311  # nosec B311 - synthetic fixture
    events: list[EventEnvelope] = []
    for day in range(days):
        for reading in range(readings_per_day):
            moment = start + timedelta(days=day, hours=reading * 24 // readings_per_day)
            watts = baseline_watts + rng.gauss(0, 40)
            events.append(
                make_envelope(
                    capability="energy.power",
                    value=round(max(watts, 0.0), 1),
                    unit="W",
                    home_id=home_id,
                    device_id="energy_meter",
                    occurred_at=moment,
                )
            )
    for index in range(spikes):
        moment = start + timedelta(days=index % max(days, 1), hours=3)
        events.append(
            make_envelope(
                capability="energy.power",
                value=spike_watts,
                unit="W",
                home_id=home_id,
                device_id="energy_meter",
                occurred_at=moment,
            )
        )
    return sorted(events, key=lambda e: e.occurred_at)


def sparse_history(count: int = 5, home_id: str = "home_001") -> list[EventEnvelope]:
    """Too little data to train anything — the insufficient-data case."""
    return [
        make_envelope(
            capability="light.power",
            value=True,
            unit=None,
            home_id=home_id,
            occurred_at=HISTORY_START + timedelta(minutes=i * 5),
        )
        for i in range(count)
    ]


def iter_days(events: list[EventEnvelope]) -> Iterator[datetime]:
    for event in events:
        yield event.occurred_at
