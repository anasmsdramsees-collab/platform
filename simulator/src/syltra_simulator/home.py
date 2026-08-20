"""Virtual home fixture — every device class required by spec §23.

All identifiers and values are synthetic. Rooms: living room, kitchen,
bedroom, bathroom, entrance, utility.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class VirtualDevice:
    device_id: str
    name: str
    room: str
    manufacturer: str = "SYLTRA Simulator"
    model: str = "virtual-1"
    entities: dict[str, dict[str, Any]] = field(default_factory=dict)
    """entity_id → initial state dict {state, attributes}."""


def _e(state: str, **attributes: Any) -> dict[str, Any]:
    return {"state": state, "attributes": attributes}


VIRTUAL_DEVICES: tuple[VirtualDevice, ...] = (
    VirtualDevice(
        device_id="sim_motion_living",
        name="Living Room Motion",
        room="living_room",
        entities={
            "binary_sensor.living_room_motion": _e("off", device_class="motion"),
            "sensor.living_room_motion_battery": _e(
                "87", device_class="battery", unit_of_measurement="%"
            ),
        },
    ),
    VirtualDevice(
        device_id="sim_presence_home",
        name="Household Presence",
        room="entrance",
        entities={"device_tracker.resident_phone": _e("home")},
    ),
    VirtualDevice(
        device_id="sim_contact_front",
        name="Front Door Contact",
        room="entrance",
        entities={"binary_sensor.front_door": _e("off", device_class="door")},
    ),
    VirtualDevice(
        device_id="sim_contact_bedroom_window",
        name="Bedroom Window Contact",
        room="bedroom",
        entities={"binary_sensor.bedroom_window": _e("off", device_class="window")},
    ),
    VirtualDevice(
        device_id="sim_climate_sensor_living",
        name="Living Room Climate Sensor",
        room="living_room",
        entities={
            "sensor.living_room_temperature": _e(
                "27.4", device_class="temperature", unit_of_measurement="°C"
            ),
            "sensor.living_room_humidity": _e(
                "41", device_class="humidity", unit_of_measurement="%"
            ),
        },
    ),
    VirtualDevice(
        device_id="sim_lux_living",
        name="Living Room Illuminance",
        room="living_room",
        entities={
            "sensor.living_room_illuminance": _e(
                "180", device_class="illuminance", unit_of_measurement="lx"
            )
        },
    ),
    VirtualDevice(
        device_id="sim_ac_living",
        name="Living Room AC",
        room="living_room",
        entities={
            "climate.living_room": _e(
                "cool", temperature=24.0, current_temperature=27.4, hvac_modes=["off", "cool"]
            )
        },
    ),
    VirtualDevice(
        device_id="sim_light_living",
        name="Living Room Light",
        room="living_room",
        entities={"light.living_room": _e("off", brightness=None)},
    ),
    VirtualDevice(
        device_id="sim_light_bedroom",
        name="Bedroom Light",
        room="bedroom",
        entities={"light.bedroom": _e("off", brightness=None)},
    ),
    VirtualDevice(
        device_id="sim_curtain_living",
        name="Living Room Curtain",
        room="living_room",
        entities={"cover.living_room_curtain": _e("open", current_position=100)},
    ),
    VirtualDevice(
        device_id="sim_lock_front",
        name="Front Door Lock",
        room="entrance",
        entities={"lock.front_door": _e("locked")},
    ),
    VirtualDevice(
        device_id="sim_leak_kitchen",
        name="Kitchen Leak Sensor",
        room="kitchen",
        entities={"binary_sensor.kitchen_leak": _e("off", device_class="moisture")},
    ),
    VirtualDevice(
        device_id="sim_water_valve",
        name="Main Water Valve",
        room="utility",
        entities={"valve.main_water": _e("open")},
    ),
    VirtualDevice(
        device_id="sim_gas_kitchen",
        name="Kitchen Gas Alarm",
        room="kitchen",
        entities={"binary_sensor.kitchen_gas": _e("off", device_class="gas")},
    ),
    VirtualDevice(
        device_id="sim_gas_valve",
        name="Gas Valve",
        room="kitchen",
        entities={"valve.gas_supply": _e("open")},
    ),
    VirtualDevice(
        device_id="sim_energy_main",
        name="Main Energy Meter",
        room="utility",
        entities={
            "sensor.home_power": _e("640", device_class="power", unit_of_measurement="W"),
            "sensor.home_energy": _e(
                "12.4", device_class="energy", unit_of_measurement="kWh"
            ),
        },
    ),
    VirtualDevice(
        device_id="sim_camera_entrance",
        name="Entrance Camera",
        room="entrance",
        entities={"camera.entrance": _e("idle")},
    ),
)


def virtual_devices() -> tuple[VirtualDevice, ...]:
    return VIRTUAL_DEVICES


VIRTUAL_HOME_STATES: dict[str, dict[str, Any]] = {
    entity_id: initial
    for device in VIRTUAL_DEVICES
    for entity_id, initial in device.entities.items()
}
