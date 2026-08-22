"""The weather this house measured, and the things it refuses to say.

Most of these tests are about absence: no forecast, no invented reading, no
average of two sensors, no confident figure derived from a stale one. A weather
block is the easiest place in a local-first product to quietly start depending
on the internet, and these are what stop it.
"""

from typing import Any

import pytest
from syltra_api_gateway.weather import (
    AIR_QUALITY,
    HUMIDITY,
    ILLUMINANCE,
    TEMPERATURE,
    heat_index_c,
    outdoor_weather,
)


def _device(
    device_id: str,
    room_id: str,
    capability: str,
    value: Any,
    unit: str | None = None,
    age: float = 5.0,
    status: str = "KNOWN",
) -> dict[str, Any]:
    return {
        "device_id": device_id,
        "room_id": room_id,
        "capabilities": {
            capability: {"value": value, "unit": unit, "status": status, "age_seconds": age}
        },
    }


def test_an_indoor_thermometer_is_not_the_sky() -> None:
    """A house without an outdoor sensor gets no weather, not a relabelled
    living room."""
    weather = outdoor_weather([_device("t", "living_room", TEMPERATURE, 22.0, "C")])
    assert weather.measured is False
    assert weather.as_view("home_1")["readings"] == {}


def test_the_payload_never_carries_a_forecast() -> None:
    view = outdoor_weather([_device("t", "outside", TEMPERATURE, 30.0, "C")]).as_view("home_1")
    assert view["forecast"] is None
    assert view["source"] == "HOME_SENSORS"


def test_two_sensors_for_the_same_thing_do_not_become_an_average() -> None:
    """Averaging a balcony and a roof produces a temperature no sensor
    measured. The fresher reading wins instead."""
    weather = outdoor_weather(
        [
            _device("roof", "roof", TEMPERATURE, 44.0, "C", age=600.0),
            _device("balcony", "balcony", TEMPERATURE, 39.0, "C", age=20.0),
        ]
    )
    assert weather.readings[TEMPERATURE].value == 39.0
    assert weather.readings[TEMPERATURE].device_id == "balcony"


def test_a_reading_the_twin_does_not_know_is_left_out() -> None:
    weather = outdoor_weather([_device("t", "outside", TEMPERATURE, None, "C", status="UNKNOWN")])
    assert weather.measured is False


@pytest.mark.parametrize(
    ("lux", "condition"),
    [(0.0, "NIGHT"), (4.0, "NIGHT"), (300.0, "TWILIGHT"), (8000.0, "CLOUD"), (94000.0, "SUN")],
)
def test_the_condition_comes_from_measured_light(lux: float, condition: str) -> None:
    weather = outdoor_weather([_device("l", "outside", ILLUMINANCE, lux, "lx")])
    assert weather.condition == condition


def test_no_condition_claims_rain() -> None:
    """A light sensor cannot tell a shower from a cloud, and nothing in the
    registry senses precipitation."""
    from syltra_api_gateway.weather import CONDITION_BANDS

    names = {name.lower() for _, name in CONDITION_BANDS}
    assert not names & {"rain", "rainy", "shower", "storm", "snow"}


def test_a_house_that_cannot_see_the_sky_says_nothing_about_it() -> None:
    weather = outdoor_weather([_device("t", "outside", TEMPERATURE, 30.0, "C")])
    assert weather.condition is None


def test_air_quality_is_banded_on_the_scale_the_capability_declares() -> None:
    assert outdoor_weather([_device("a", "outside", AIR_QUALITY, 20.0)]).air_band == "GOOD"
    assert outdoor_weather([_device("a", "outside", AIR_QUALITY, 68.0)]).air_band == "MODERATE"
    assert outdoor_weather([_device("a", "outside", AIR_QUALITY, 460.0)]).air_band == "HAZARDOUS"


def test_dry_heat_feels_cooler_than_the_thermometer_says() -> None:
    """A Gulf afternoon at 12% humidity: without the low-humidity adjustment
    the panel would overstate it by several degrees."""
    felt = heat_index_c(41.0, 12.0)
    assert felt is not None
    assert felt < 41.0


def test_humid_heat_feels_hotter() -> None:
    felt = heat_index_c(32.0, 80.0)
    assert felt is not None
    assert felt > 32.0


def test_a_cold_night_gets_no_feels_like_because_there_is_no_wind_sensor() -> None:
    """Wind chill is the honest counterpart and it needs an anemometer this
    platform has no capability for. Guessing at wind would invent the input
    that matters most."""
    assert heat_index_c(4.0, 60.0) is None


def test_a_stale_input_withdraws_the_feels_like_rather_than_ageing_it() -> None:
    weather = outdoor_weather(
        [
            _device("t", "outside", TEMPERATURE, 41.0, "C", age=10.0),
            _device("h", "outside", HUMIDITY, 12.0, "%", age=5000.0),
        ]
    )
    assert weather.readings[HUMIDITY].stale is True
    assert weather.feels_like_c is None


def test_a_stale_reading_is_still_shown_with_its_age() -> None:
    """A blank where a temperature used to be reads as a broken panel."""
    view = outdoor_weather([_device("t", "outside", TEMPERATURE, 34.0, "C", age=5000.0)]).as_view(
        "home_1"
    )
    reading = view["readings"][TEMPERATURE]
    assert reading["stale"] is True
    assert reading["value"] == 34.0
    assert reading["age_seconds"] == 5000.0
