"""Energy over time, with its gaps intact (spec §17.11, §27 criterion 9).

Almost every test here is about a hole in the data. A trend chart that draws a
smooth line through a period nothing reported in is the single most common way
an energy dashboard lies, and §17.11 forbids it in words — this is the code that
makes the words true.
"""

from datetime import UTC, datetime, timedelta

import pytest
from syltra_api_gateway.energy import EnergyBucket, EnergyHistory, Resolution

pytestmark = pytest.mark.contract

NOW = datetime(2026, 8, 20, 12, 0, tzinfo=UTC)
HOME = "home_energy"


def steady(
    history: EnergyHistory, hours: int, watts: float = 800.0, every_minutes: int = 5
) -> None:
    for step in range(hours * (60 // every_minutes)):
        history.record(HOME, watts, NOW + timedelta(minutes=step * every_minutes))


# ── the rule the whole module exists for ──


def test_a_bucket_with_no_samples_cannot_be_built() -> None:
    with pytest.raises(ValueError, match="a gap, not a measurement"):
        EnergyBucket(
            start=NOW,
            resolution=Resolution.HOUR,
            watts=0.0,
            minimum=0.0,
            maximum=0.0,
            samples=0,
            expected_samples=12,
        )


def test_an_hour_nothing_reported_in_is_missing_rather_than_zero() -> None:
    """The lie this module exists to prevent.

    A meter silent from 13:00 to 14:00 did not consume zero watts; it consumed
    an unknown amount. Reporting zero would put a floor in the chart that
    nobody measured.
    """
    history = EnergyHistory()
    steady(history, hours=1)
    # Nothing for the second hour, then readings resume.
    for step in range(12):
        history.record(HOME, 900.0, NOW + timedelta(hours=2, minutes=step * 5))

    series = history.series(HOME, Resolution.HOUR, NOW, NOW + timedelta(hours=3))

    starts = [bucket.start for bucket in series.buckets]
    assert NOW + timedelta(hours=1) not in starts
    assert series.missing == (NOW + timedelta(hours=1),)
    assert all(bucket.watts > 0 for bucket in series.buckets)


def test_the_series_says_it_estimated_nothing() -> None:
    history = EnergyHistory()
    steady(history, hours=2)
    view = history.series(HOME, Resolution.HOUR, NOW, NOW + timedelta(hours=2)).as_view()
    assert view["estimated"] is False
    assert "missing" in view


def test_no_kilowatt_hours_are_offered() -> None:
    """Converting a mean of unevenly spaced samples to kWh is a guess.

    Cumulative energy is what `energy.consumption` is for, and inventing it from
    power readings is the same mistake as filling a gap.
    """
    history = EnergyHistory()
    steady(history, hours=1)
    view = history.series(HOME, Resolution.HOUR, NOW, NOW + timedelta(hours=1)).as_view()
    serialized = str(view)
    assert "kwh" not in serialized.lower()
    assert "cost" not in serialized.lower()


# ── coverage tells you how much to trust a bucket ──


def test_coverage_falls_when_a_meter_reports_less_often() -> None:
    history = EnergyHistory()
    # Twelve readings in the first hour, two in the second.
    steady(history, hours=1)
    for step in range(2):
        history.record(HOME, 800.0, NOW + timedelta(hours=1, minutes=step * 5))

    series = history.series(HOME, Resolution.HOUR, NOW, NOW + timedelta(hours=2))
    full, sparse = series.buckets
    assert full.coverage == 1.0
    assert sparse.coverage < 0.3


def test_the_whole_series_reports_how_much_of_it_is_real() -> None:
    history = EnergyHistory()
    steady(history, hours=1)
    series = history.series(HOME, Resolution.HOUR, NOW, NOW + timedelta(hours=4))
    assert series.covered == pytest.approx(0.25)


# ── the arithmetic ──


def test_a_bucket_carries_the_range_as_well_as_the_mean() -> None:
    """A mean of 800 W hides a fridge compressor starting.

    The minimum and maximum are what makes a spike visible at all once an hour
    of readings is reduced to one number.
    """
    history = EnergyHistory()
    for watts in (100.0, 800.0, 2400.0):
        history.record(HOME, watts, NOW + timedelta(minutes=len(str(watts))))
    bucket = history.series(HOME, Resolution.HOUR, NOW, NOW + timedelta(hours=1)).buckets[0]
    assert bucket.minimum == 100.0
    assert bucket.maximum == 2400.0
    assert 100.0 < bucket.watts < 2400.0


def test_a_replayed_buffer_does_not_corrupt_the_series() -> None:
    """A device that reconnects and replays arrives out of order.

    Appending blindly would put an old reading after a new one, and every
    bucket boundary computed after it would be wrong.
    """
    history = EnergyHistory()
    history.record(HOME, 900.0, NOW + timedelta(minutes=30))
    history.record(HOME, 100.0, NOW + timedelta(minutes=5))
    series = history.series(HOME, Resolution.HOUR, NOW, NOW + timedelta(hours=1))
    assert series.buckets[0].samples == 2
    assert series.buckets[0].minimum == 100.0


def test_a_device_filter_narrows_to_one_meter() -> None:
    history = EnergyHistory()
    history.record(HOME, 500.0, NOW, device_id="meter_home")
    history.record(HOME, 60.0, NOW, device_id="plug_fridge")
    whole = history.series(HOME, Resolution.HOUR, NOW, NOW + timedelta(hours=1))
    fridge = history.series(
        HOME, Resolution.HOUR, NOW, NOW + timedelta(hours=1), device_id="plug_fridge"
    )
    assert whole.buckets[0].samples == 2
    assert fridge.buckets[0].samples == 1
    assert fridge.buckets[0].watts == 60.0


# ── a household with no history ──


def test_a_home_that_has_never_reported_is_empty_not_zero() -> None:
    history = EnergyHistory()
    series = history.series(HOME, Resolution.HOUR, NOW, NOW + timedelta(hours=2))
    assert series.buckets == ()
    assert len(series.missing) == 2
    assert history.earliest(HOME) is None
