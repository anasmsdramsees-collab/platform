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
    home_weather,
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
    """A house without an outdoor sensor gets no outdoor temperature, not a
    relabelled living room. The reading still appears — as the indoor half,
    with the room it was taken in on it."""
    weather = home_weather([_device("t", "living_room", TEMPERATURE, 22.0, "C")])
    assert weather.readings == {}
    assert weather.condition is None
    assert weather.indoor is not None
    assert weather.indoor.room_id == "living_room"


def test_the_indoor_temperature_is_one_room_rather_than_an_average() -> None:
    """Averaging a shaded bedroom with a sunlit majlis produces a temperature no
    sensor measured and no room feels like."""
    weather = home_weather(
        [
            _device("a", "majlis", TEMPERATURE, 31.0, "C", age=90.0),
            _device("b", "bedroom", TEMPERATURE, 21.0, "C", age=10.0),
        ]
    )
    assert weather.indoor is not None
    assert weather.indoor.value == 21.0
    assert weather.indoor.room_id == "bedroom"
    # And it says how many rooms it is not speaking for.
    assert weather.indoor_rooms == 2


def test_the_same_house_always_shows_the_same_room() -> None:
    """A tie on freshness breaks on the room name rather than on whichever
    device the twin happened to return first — a panel whose indoor reading
    hops between rooms every five seconds is a panel nobody trusts."""
    devices = [
        _device("a", "majlis", TEMPERATURE, 31.0, "C", age=10.0),
        _device("b", "bedroom", TEMPERATURE, 21.0, "C", age=10.0),
    ]
    first = home_weather(devices).indoor
    second = home_weather(list(reversed(devices))).indoor
    assert first is not None and second is not None
    assert first.room_id == second.room_id == "bedroom"


def test_the_difference_is_the_number_a_household_acts_on() -> None:
    weather = home_weather(
        [
            _device("out", "outside", TEMPERATURE, 41.0, "C"),
            _device("in", "living_room", TEMPERATURE, 24.0, "C"),
        ]
    )
    assert weather.difference_c == 17.0


def test_a_difference_is_not_computed_across_two_different_afternoons() -> None:
    weather = home_weather(
        [
            _device("out", "outside", TEMPERATURE, 41.0, "C", age=10.0),
            _device("in", "living_room", TEMPERATURE, 24.0, "C", age=5000.0),
        ]
    )
    assert weather.indoor is not None
    assert weather.indoor.stale is True
    assert weather.difference_c is None


def test_the_payload_never_carries_a_forecast() -> None:
    view = home_weather([_device("t", "outside", TEMPERATURE, 30.0, "C")]).as_view("home_1")
    assert view["forecast"] is None
    assert view["source"] == "HOME_SENSORS"


def test_two_sensors_for_the_same_thing_do_not_become_an_average() -> None:
    """Averaging a balcony and a roof produces a temperature no sensor
    measured. The fresher reading wins instead."""
    weather = home_weather(
        [
            _device("roof", "roof", TEMPERATURE, 44.0, "C", age=600.0),
            _device("balcony", "balcony", TEMPERATURE, 39.0, "C", age=20.0),
        ]
    )
    assert weather.readings[TEMPERATURE].value == 39.0
    assert weather.readings[TEMPERATURE].device_id == "balcony"


def test_a_reading_the_twin_does_not_know_is_left_out() -> None:
    weather = home_weather([_device("t", "outside", TEMPERATURE, None, "C", status="UNKNOWN")])
    assert weather.measured is False


@pytest.mark.parametrize(
    ("lux", "condition"),
    [(0.0, "NIGHT"), (4.0, "NIGHT"), (300.0, "TWILIGHT"), (8000.0, "CLOUD"), (94000.0, "SUN")],
)
def test_the_condition_comes_from_measured_light(lux: float, condition: str) -> None:
    weather = home_weather([_device("l", "outside", ILLUMINANCE, lux, "lx")])
    assert weather.condition == condition


def test_no_condition_claims_rain() -> None:
    """A light sensor cannot tell a shower from a cloud, and nothing in the
    registry senses precipitation."""
    from syltra_api_gateway.weather import CONDITION_BANDS

    names = {name.lower() for _, name in CONDITION_BANDS}
    assert not names & {"rain", "rainy", "shower", "storm", "snow"}


def test_a_house_that_cannot_see_the_sky_says_nothing_about_it() -> None:
    weather = home_weather([_device("t", "outside", TEMPERATURE, 30.0, "C")])
    assert weather.condition is None


def test_air_quality_is_banded_on_the_scale_the_capability_declares() -> None:
    assert home_weather([_device("a", "outside", AIR_QUALITY, 20.0)]).air_band == "GOOD"
    assert home_weather([_device("a", "outside", AIR_QUALITY, 68.0)]).air_band == "MODERATE"
    assert home_weather([_device("a", "outside", AIR_QUALITY, 460.0)]).air_band == "HAZARDOUS"


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
    weather = home_weather(
        [
            _device("t", "outside", TEMPERATURE, 41.0, "C", age=10.0),
            _device("h", "outside", HUMIDITY, 12.0, "%", age=5000.0),
        ]
    )
    assert weather.readings[HUMIDITY].stale is True
    assert weather.feels_like_c is None


def test_a_stale_reading_is_still_shown_with_its_age() -> None:
    """A blank where a temperature used to be reads as a broken panel."""
    view = home_weather([_device("t", "outside", TEMPERATURE, 34.0, "C", age=5000.0)]).as_view(
        "home_1"
    )
    reading = view["readings"][TEMPERATURE]
    assert reading["stale"] is True
    assert reading["value"] == 34.0
    assert reading["age_seconds"] == 5000.0
