"""A house that does not exist, so the tests do not need one.

The mock answers in the same shapes the platform answers in, including the
fields that matter to SELLA's honesty rules: `operable` says whether this caller
may press it, `verified` says whether the device confirmed, and `status` says
whether the reading is even known.
"""

from typing import Any


class MockSyltraClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Any]] = []
        self._state: dict[tuple[str, str], Any] = {
            ("light_majlis", "light.power"): False,
            ("light_living", "light.power"): True,
            ("ac_living", "climate.target_temperature"): 24.0,
            ("curtain_living", "cover.position"): 60.0,
            ("door_main", "lock.state"): "locked",
        }
        self._devices = [
            ("light_majlis", "majlis", "إضاءة المجلس", "light.power", "COMFORT", True),
            ("light_living", "living_room", "إضاءة الصالة", "light.power", "COMFORT", True),
            (
                "ac_living",
                "living_room",
                "مكيّف الصالة",
                "climate.target_temperature",
                "COMFORT",
                True,
            ),
            ("curtain_living", "living_room", "ستارة الصالة", "cover.position", "COMFORT", True),
            (
                "temp_living",
                "living_room",
                "حرارة الصالة",
                "environment.temperature",
                "COMFORT",
                False,
            ),
            (
                "gas_kitchen",
                "kitchen",
                "كاشف الغاز",
                "safety.gas_alarm",
                "LIFE_SAFETY_CRITICAL",
                False,
            ),
            ("door_main", "entrance", "الباب الرئيسي", "lock.state", "SECURITY_SENSITIVE", True),
        ]

    async def devices(self) -> list[dict[str, Any]]:
        out = []
        for device_id, room, name, capability, _cls, operable in self._devices:
            value = self._state.get((device_id, capability))
            if capability == "environment.temperature":
                value = 24.1
            if capability == "safety.gas_alarm":
                value = False
            out.append(
                {
                    "device_id": device_id,
                    "room_id": room,
                    "name": name,
                    "capabilities": {
                        capability: {
                            "value": value,
                            "status": "KNOWN",
                            "operable": operable,
                            "unit": None,
                        }
                    },
                }
            )
        return out

    async def rooms(self) -> list[dict[str, Any]]:
        seen: dict[str, int] = {}
        for _id, room, *_ in self._devices:
            seen[room] = seen.get(room, 0) + 1
        return [{"room_id": r, "device_count": n} for r, n in sorted(seen.items())]

    async def scenes(self) -> list[dict[str, Any]]:
        return [
            {
                "scene_id": "11111111-1111-1111-1111-111111111111",
                "name": "وضع النوم",
                "summary": "home:light.power=False",
                "activatable": True,
            }
        ]

    async def risks(self) -> dict[str, Any]:
        return {"cases": []}

    async def energy(self) -> dict[str, Any]:
        return {"buckets": [{"watts": 1420.0, "samples": 12, "coverage": 1.0}], "missing": []}

    async def set_capability(self, device_id: str, capability: str, value: Any) -> dict[str, Any]:
        self.calls.append(("set", (device_id, capability, value)))
        self._state[(device_id, capability)] = value
        return {
            "device_id": device_id,
            "capability": capability,
            "status": "SUCCEEDED",
            "verified": True,
            "reasons": ["تم التأكيد من الجهاز"],
        }

    async def activate_scene(self, scene_id: str) -> dict[str, Any]:
        self.calls.append(("scene", scene_id))
        return {"scene_id": scene_id, "name": "وضع النوم", "fully_carried_out": True, "steps": []}


class FailingSyltraClient(MockSyltraClient):
    """A hub that accepts the command and cannot confirm it.

    The case §14.1 cares about: the device did not answer, so SELLA must not say
    it did.
    """

    async def set_capability(self, device_id: str, capability: str, value: Any) -> dict[str, Any]:
        self.calls.append(("set", (device_id, capability, value)))
        return {
            "device_id": device_id,
            "capability": capability,
            "status": "SUCCEEDED",
            "verified": False,
            "reasons": ["لم يؤكد الجهاز"],
        }
