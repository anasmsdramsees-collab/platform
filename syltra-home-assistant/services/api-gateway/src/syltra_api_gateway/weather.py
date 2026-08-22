"""The weather where the house actually is, from the household's own sensors.

A weather app answers "what is it like outside" with a reading taken at an
airport some kilometres away and a forecast fetched from a service on the
internet. A hub with an outdoor sensor can answer the same question about *this*
house — this courtyard, this side of this street, in shade or in sun — and can
answer it with the line to the outside world cut, which is the promise the rest
of the platform makes (§0, ADR-001).

So this composes what the house measured, and refuses to compose anything else.

## No forecast

Everything here is a reading with a timestamp on it. There is no "later today"
and no "tomorrow", because nothing in this house can measure tomorrow. A
forecast needs a network and somebody else's service, and a panel that shows one
begins lying the moment the line is down — quietly, in the same typeface as the
true numbers beside it. If a household wants a forecast it belongs behind the
cloud connector, drawn differently, and labelled as coming from somewhere else.

## No invented reading

A house with no outdoor thermometer gets no temperature — not an indoor one
relabelled, not a figure carried over from a room. ``measured`` is false when
there is no outdoor sensor at all, and the panel shows nothing rather than
something.

## Two temperatures, and the room one of them is in

"41 outside" is half a fact. The half a household acts on is the difference:
whether to open a window, whether the air conditioning is winning, whether the
room somebody is about to walk into is worse than the one they are leaving.

So the payload carries an indoor temperature beside the outdoor one — and names
the room it came from. It is one room's thermometer, not an average of the
house: averaging a shaded bedroom with a sunlit majlis produces a temperature no
sensor measured and no room feels like. A house with thermometers in four rooms
still gets one number here, labelled with which room, and the console is where
somebody compares all four.

## Stale is shown, not hidden

Environment readings are stale past their freshness budget (§10.3). A stale
reading is still displayed, with its age, rather than dropped: "34°, twenty
minutes ago" is useful, and a blank tile where a temperature used to be reads as
a broken panel. What it must never do is look current.

## What light can and cannot say

The condition comes from measured illuminance, and the wording stays inside what
that measurement supports. Direct sun outdoors is tens of thousands of lux;
overcast daylight is a few thousand; twilight is tens. Those bands are the
condition. **Rain is not among them** — a light sensor cannot tell a rain shower
from a cloud, and no capability in the registry senses precipitation. A panel
saying "cloudy" while it rains is a panel that was honest about what it knew.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from math import sqrt
from typing import Any, Final

from syltra_contracts.capability_definitions import CAPABILITY_DEFINITIONS

#: Rooms whose sensors are outdoors. Room identifiers come from Home Assistant's
#: areas, so this is a naming convention rather than a fact the twin knows — a
#: room flagged as outdoor belongs in the twin, and until it is there, a house
#: whose outdoor area is called something else simply shows no weather rather
#: than showing a bedroom's temperature as the sky's.
OUTDOOR_ROOMS: Final[frozenset[str]] = frozenset(
    {"outside", "outdoor", "outdoors", "garden", "yard", "balcony", "terrace", "roof"}
)

TEMPERATURE: Final = "environment.temperature"
HUMIDITY: Final = "environment.humidity"
ILLUMINANCE: Final = "environment.illuminance"
AIR_QUALITY: Final = "environment.air_quality"

WEATHER_CAPABILITIES: Final[tuple[str, ...]] = (TEMPERATURE, HUMIDITY, ILLUMINANCE, AIR_QUALITY)

#: Illuminance in lux, and the condition each band supports. Upper bound first,
#: brightest last; the basis for each number is in the module docstring.
CONDITION_BANDS: Final[tuple[tuple[float, str], ...]] = (
    (5.0, "NIGHT"),
    (1000.0, "TWILIGHT"),
    (25000.0, "CLOUD"),
    (float("inf"), "SUN"),
)

#: Air quality index bands, on the 0-500 scale the capability declares.
AIR_BANDS: Final[tuple[tuple[float, str], ...]] = (
    (50.0, "GOOD"),
    (100.0, "MODERATE"),
    (150.0, "POOR"),
    (200.0, "UNHEALTHY"),
    (300.0, "VERY_UNHEALTHY"),
    (float("inf"), "HAZARDOUS"),
)

#: Below this the heat index formula does not apply, and the honest alternative
#: — wind chill — needs an anemometer this platform has no capability for. So a
#: cold house gets a temperature and no "feels like" at all.
HEAT_INDEX_FROM_C: Final = 26.7

#: A "feels like" within this of the reading is noise dressed as insight.
FEELS_LIKE_MARGIN_C: Final = 1.0


def _band(value: float, bands: tuple[tuple[float, str], ...]) -> str:
    for upper, name in bands:
        if value <= upper:
            return name
    return bands[-1][1]


def heat_index_c(temperature_c: float, humidity_percent: float) -> float | None:
    """Apparent temperature from heat and humidity (NOAA's Rothfusz regression).

    Returns ``None`` below the range the regression covers rather than
    extrapolating it: the formula is a fit to warm, humid conditions and says
    nothing useful about a cold night. There is no wind-chill counterpart
    because there is no wind capability — a hub that guessed at wind would be
    inventing the one input that matters most.
    """
    if temperature_c < HEAT_INDEX_FROM_C:
        return None
    t = temperature_c * 9 / 5 + 32
    r = humidity_percent
    hi = (
        -42.379
        + 2.04901523 * t
        + 10.14333127 * r
        - 0.22475541 * t * r
        - 0.00683783 * t * t
        - 0.05481717 * r * r
        + 0.00122874 * t * t * r
        + 0.00085282 * t * r * r
        - 0.00000199 * t * t * r * r
    )
    # Dry heat feels cooler than the regression's midrange fit, and a Gulf
    # summer at 12% humidity is exactly that case: without this the panel would
    # overstate an August afternoon by several degrees.
    if r < 13 and 80 <= t <= 112:
        hi -= ((13 - r) / 4) * sqrt((17 - abs(t - 95)) / 17)
    elif r > 85 and 80 <= t <= 87:
        hi += ((r - 85) / 10) * ((87 - t) / 5)
    return (hi - 32) * 5 / 9


@dataclass(frozen=True)
class Measurement:
    """One outdoor reading, with how old it is and which sensor gave it."""

    capability: str
    value: float
    unit: str | None
    age_seconds: float
    device_id: str
    room_id: str = ""

    @property
    def stale(self) -> bool:
        return self.age_seconds > CAPABILITY_DEFINITIONS[self.capability].freshness_seconds

    def as_view(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "unit": self.unit,
            "age_seconds": round(self.age_seconds, 1),
            "stale": self.stale,
            "device_id": self.device_id,
            "room_id": self.room_id,
        }


@dataclass(frozen=True)
class Weather:
    """What the house can say about outside, and nothing further."""

    readings: Mapping[str, Measurement]
    indoor: Measurement | None = None
    indoor_rooms: int = 0
    """How many rooms have a thermometer, so nothing pretends one speaks for
    the house."""

    @property
    def measured(self) -> bool:
        return bool(self.readings) or self.indoor is not None

    @property
    def difference_c(self) -> float | None:
        """How much colder it is inside, in degrees, or None.

        The number a household actually acts on: whether to open a window,
        whether the air conditioning is winning. Withdrawn when either side is
        stale, because a difference between a current reading and an hour-old
        one is arithmetic on two different afternoons.
        """
        outside = self.readings.get(TEMPERATURE)
        if outside is None or self.indoor is None:
            return None
        if outside.stale or self.indoor.stale:
            return None
        return round(outside.value - self.indoor.value, 1)

    @property
    def condition(self) -> str | None:
        light = self.readings.get(ILLUMINANCE)
        return None if light is None else _band(light.value, CONDITION_BANDS)

    @property
    def air_band(self) -> str | None:
        air = self.readings.get(AIR_QUALITY)
        return None if air is None else _band(air.value, AIR_BANDS)

    @property
    def feels_like_c(self) -> float | None:
        """Only when both inputs are current, and only when it differs.

        A "feels like" computed from an hour-old humidity reading is a number
        with a confidence it has not earned, so a stale input withdraws the
        figure rather than ageing it.
        """
        temperature = self.readings.get(TEMPERATURE)
        humidity = self.readings.get(HUMIDITY)
        if temperature is None or humidity is None:
            return None
        if temperature.stale or humidity.stale:
            return None
        felt = heat_index_c(temperature.value, humidity.value)
        if felt is None or abs(felt - temperature.value) < FEELS_LIKE_MARGIN_C:
            return None
        return round(felt, 1)

    def as_view(self, home_id: str) -> dict[str, Any]:
        return {
            "home_id": home_id,
            # Said in the payload rather than left for a reader to infer, because
            # every other product's weather block means "somewhere near you,
            # from the internet" and this one does not.
            "source": "HOME_SENSORS",
            "forecast": None,
            "measured": self.measured,
            "condition": self.condition,
            "air_band": self.air_band,
            "feels_like_c": self.feels_like_c,
            "indoor": self.indoor.as_view() if self.indoor is not None else None,
            "indoor_rooms": self.indoor_rooms,
            "difference_c": self.difference_c,
            "readings": {name: m.as_view() for name, m in sorted(self.readings.items())},
        }


def _reading(
    device: Mapping[str, Any], capability: str, room_id: str
) -> Measurement | None:
    capabilities = device.get("capabilities")
    if not isinstance(capabilities, Mapping):
        return None
    reading = capabilities.get(capability)
    if not isinstance(reading, Mapping) or reading.get("status") != "KNOWN":
        return None
    value = reading.get("value")
    if not isinstance(value, int | float) or isinstance(value, bool):
        return None
    return Measurement(
        capability=capability,
        value=float(value),
        unit=reading.get("unit"),
        age_seconds=float(reading.get("age_seconds") or 0.0),
        device_id=str(device.get("device_id", "")),
        room_id=room_id,
    )


def home_weather(devices: Iterable[Mapping[str, Any]]) -> Weather:
    """Read the weather off the devices the twin knows about.

    Where two sensors report the same thing outdoors — a balcony thermometer and
    one on the roof — the fresher wins. Averaging them would produce a
    temperature no sensor measured, which is the one thing this module will not
    do; the same reasoning picks a single room for the indoor figure rather than
    a mean of the house.
    """
    outdoor: dict[str, Measurement] = {}
    indoor: Measurement | None = None
    rooms_with_thermometer: set[str] = set()

    for device in devices:
        room_id = str(device.get("room_id") or "")
        if room_id.lower() in OUTDOOR_ROOMS:
            for name in WEATHER_CAPABILITIES:
                found = _reading(device, name, room_id)
                if found is None:
                    continue
                current = outdoor.get(name)
                if current is None or found.age_seconds < current.age_seconds:
                    outdoor[name] = found
            continue

        inside = _reading(device, TEMPERATURE, room_id)
        if inside is None:
            continue
        rooms_with_thermometer.add(room_id)
        # Freshest wins, and ties break on the room name so the same house
        # always shows the same room rather than whichever dict came first.
        if (
            indoor is None
            or inside.age_seconds < indoor.age_seconds
            or (inside.age_seconds == indoor.age_seconds and inside.room_id < indoor.room_id)
        ):
            indoor = inside

    return Weather(
        readings=outdoor,
        indoor=indoor,
        indoor_rooms=len(rooms_with_thermometer),
    )
