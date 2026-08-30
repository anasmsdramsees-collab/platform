"""The twelve home tools of phase one.

Two rules shape all of them.

**The model never sends an entity id.** It sends a room and a thing, in Arabic,
and `resolve` matches that against the devices the platform says exist and says
this caller may operate. §13.2 asks for an entity map; the platform already has
one, so this resolves against it rather than keeping a second copy that drifts.

**A command is not done until the device says so.** Every write returns the
platform's `verified` flag, and a tool that cannot confirm reports failure. A
model told "SUCCEEDED" will tell the household the light is on.
"""

import unicodedata
from typing import Any

from integrations.syltra.client import SyltraClient
from policies.risk import RiskLevel, risk_for_safety_class
from sella_core.errors import ToolError
from tools.registry import Tool, ToolRegistry

#: What a person says, and the capability it means.
CAPABILITY_WORDS: dict[str, tuple[str, ...]] = {
    "light.power": ("لمبة", "لمبه", "إضاءة", "اضاءة", "نور", "الانوار", "الأنوار", "light"),
    "climate.target_temperature": ("مكيف", "مكيّف", "تكييف", "حرارة", "ac"),
    "cover.position": ("ستارة", "ستاره", "ستائر", "شيش", "curtain"),
    "switch.power": ("قابس", "مفتاح", "بلاق", "switch", "plug"),
    "lock.state": ("قفل", "باب", "lock", "door"),
}

#: Room words, including the ones a household actually uses.
ROOM_WORDS: dict[str, tuple[str, ...]] = {
    "majlis": ("المجلس", "مجلس", "غرفة الضيوف", "الصالة الخارجية", "majlis"),
    "living_room": ("الصالة", "صالة", "المعيشة", "غرفة المعيشة", "living"),
    "bedroom": ("غرفة النوم", "النوم", "bedroom"),
    "kitchen": ("المطبخ", "مطبخ", "kitchen"),
    "entrance": ("المدخل", "الباب", "entrance"),
    "hall": ("الممر", "hall"),
}


def _fold(text: str) -> str:
    """Arabic as people type it: no diacritics, one shape per letter.

    Without this, "مكيّف" and "مكيف" are different strings and the household is
    told the room has no air conditioning.
    """
    stripped = "".join(
        c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)
    )
    for a, b in (("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ة", "ه"), ("ى", "ي"), ("ﻻ", "لا")):
        stripped = stripped.replace(a, b)
    return stripped.strip().lower()


def _match(word: str, candidates: tuple[str, ...]) -> bool:
    folded = _fold(word)
    return any(_fold(c) in folded or folded in _fold(c) for c in candidates)


def capability_from_words(text: str) -> str | None:
    for capability, words in CAPABILITY_WORDS.items():
        if _match(text, words):
            return capability
    return None


def room_from_words(text: str) -> str | None:
    for room, words in ROOM_WORDS.items():
        if _match(text, words):
            return room
    return None


async def resolve(
    client: SyltraClient, *, thing: str, room: str | None = None
) -> tuple[str, str, str]:
    """Find one device and capability, or refuse and say why.

    Returns `(device_id, capability, display_name)`.
    """
    capability = capability_from_words(thing)
    if capability is None:
        raise ToolError(
            code="UNKNOWN_THING",
            detail=f"no capability matches {thing!r}",
            spoken=f"ما عرفت تقصد شنو بـ{thing}.",
        )
    wanted_room = room_from_words(room) if room else None

    matches = []
    for device in await client.devices():
        reading = (device.get("capabilities") or {}).get(capability)
        if reading is None:
            continue
        if wanted_room and device.get("room_id") != wanted_room:
            continue
        if _match(thing, (device.get("name") or "",)) or wanted_room or not room:
            matches.append((device, reading))

    if not matches:
        where = f" في {room}" if room else ""
        raise ToolError(
            code="NO_SUCH_DEVICE",
            detail=f"{capability} not found in {wanted_room or 'home'}",
            spoken=f"ما لقيت {thing}{where}.",
        )
    if len(matches) > 1 and not wanted_room:
        rooms = "، ".join(sorted({str(d.get("room_id")) for d, _ in matches}))
        raise ToolError(
            code="AMBIGUOUS_DEVICE",
            detail=f"{len(matches)} candidates",
            spoken=f"في أكثر من واحد: {rooms}. أي وحدة؟",
        )

    device, _reading = matches[0]
    return str(device["device_id"]), capability, str(device.get("name") or device["device_id"])


def _verified(result: dict[str, Any]) -> bool:
    return result.get("status") == "SUCCEEDED" and bool(result.get("verified"))


def build_registry(client: SyltraClient) -> ToolRegistry:
    registry = ToolRegistry()
    string = {"type": "string"}

    async def get_home_state(_: dict[str, Any]) -> dict[str, Any]:
        devices = await client.devices()
        return {
            "device_count": len(devices),
            "rooms": sorted({str(d.get("room_id")) for d in devices if d.get("room_id")}),
            "devices": [
                {
                    "name": d.get("name"),
                    "room": d.get("room_id"),
                    "readings": {
                        c: r.get("value")
                        for c, r in (d.get("capabilities") or {}).items()
                        if r.get("status") == "KNOWN"
                    },
                }
                for d in devices
            ],
        }

    async def get_room_state(args: dict[str, Any]) -> dict[str, Any]:
        room = room_from_words(str(args.get("room", "")))
        if room is None:
            raise ToolError(
                code="UNKNOWN_ROOM",
                detail=str(args.get("room")),
                spoken="ما عرفت أي غرفة تقصد.",
            )
        devices = [d for d in await client.devices() if d.get("room_id") == room]
        return {"room": room, "device_count": len(devices), "devices": devices}

    async def list_available_devices(_: dict[str, Any]) -> dict[str, Any]:
        devices = await client.devices()
        return {
            "devices": [
                {
                    "name": d.get("name"),
                    "room": d.get("room_id"),
                    "operable": [
                        c for c, r in (d.get("capabilities") or {}).items() if r.get("operable")
                    ],
                }
                for d in devices
            ]
        }

    async def _write(thing: str, room: str | None, capability_value: Any) -> dict[str, Any]:
        device_id, capability, name = await resolve(client, thing=thing, room=room)
        result = await client.set_capability(device_id, capability, capability_value)
        done = _verified(result)
        return {
            "device": name,
            "capability": capability,
            "value": capability_value,
            # The field the model is instructed to read before claiming success.
            "carried_out": done,
            "reason": "; ".join(result.get("reasons", [])) if not done else "",
        }

    async def control_light(args: dict[str, Any]) -> dict[str, Any]:
        return await _write(str(args.get("thing", "إضاءة")), args.get("room"), bool(args["on"]))

    async def set_light_brightness(args: dict[str, Any]) -> dict[str, Any]:
        level = int(args["brightness"])
        if not 0 <= level <= 100:
            raise ToolError(code="OUT_OF_RANGE", detail=str(level), spoken="السطوع من صفر إلى مئة.")
        device_id, _c, name = await resolve(client, thing="إضاءة", room=args.get("room"))
        result = await client.set_capability(device_id, "light.brightness", level)
        return {"device": name, "brightness": level, "carried_out": _verified(result)}

    async def set_ac_temperature(args: dict[str, Any]) -> dict[str, Any]:
        degrees = float(args["temperature"])
        if not 16 <= degrees <= 30:
            raise ToolError(
                code="OUT_OF_RANGE",
                detail=str(degrees),
                spoken="درجة المكيّف من ١٦ إلى ٣٠.",
            )
        return await _write("مكيّف", args.get("room"), degrees)

    async def set_ac_mode(args: dict[str, Any]) -> dict[str, Any]:
        mode = str(args["mode"])
        allowed = {"off", "cool", "heat", "auto", "dry", "fan_only"}
        if mode not in allowed:
            raise ToolError(code="OUT_OF_RANGE", detail=mode, spoken="وضع المكيّف غير معروف.")
        device_id, _c, name = await resolve(client, thing="مكيّف", room=args.get("room"))
        result = await client.set_capability(device_id, "climate.mode", mode)
        return {"device": name, "mode": mode, "carried_out": _verified(result)}

    async def control_curtain(args: dict[str, Any]) -> dict[str, Any]:
        position = int(args["position"])
        if not 0 <= position <= 100:
            raise ToolError(
                code="OUT_OF_RANGE", detail=str(position), spoken="فتح الستارة من صفر إلى مئة."
            )
        return await _write("ستارة", args.get("room"), position)

    async def activate_scene(args: dict[str, Any]) -> dict[str, Any]:
        wanted = _fold(str(args["scene"]))
        for scene in await client.scenes():
            if wanted in _fold(str(scene.get("name", ""))):
                if not scene.get("activatable", False):
                    raise ToolError(
                        code="SCENE_NOT_ALLOWED",
                        detail=str(scene.get("scene_id")),
                        spoken="ما عندي صلاحية أشغّل هذا السيناريو.",
                    )
                result = await client.activate_scene(str(scene["scene_id"]))
                return {
                    "scene": scene.get("name"),
                    "carried_out": bool(result.get("fully_carried_out")),
                    "steps": len(result.get("steps", [])),
                }
        raise ToolError(
            code="NO_SUCH_SCENE",
            detail=str(args["scene"]),
            spoken=f"ما عندي سيناريو اسمه {args['scene']}.",
        )

    async def get_sensor_state(args: dict[str, Any]) -> dict[str, Any]:
        wanted = str(args.get("sensor", ""))
        out = []
        for device in await client.devices():
            for capability, reading in (device.get("capabilities") or {}).items():
                if not capability.startswith(("environment.", "occupancy.", "safety.")):
                    continue
                if wanted and not (
                    _match(wanted, (str(device.get("name") or ""),)) or _fold(wanted) in capability
                ):
                    continue
                out.append(
                    {
                        "name": device.get("name"),
                        "room": device.get("room_id"),
                        "capability": capability,
                        "value": reading.get("value"),
                        # An unknown reading is reported as unknown. A sensor
                        # that has gone quiet must not read as "all clear".
                        "known": reading.get("status") == "KNOWN",
                    }
                )
        if not out:
            raise ToolError(code="NO_SUCH_SENSOR", detail=wanted, spoken=f"ما لقيت حسّاس {wanted}.")
        return {"sensors": out}

    async def get_security_summary(_: dict[str, Any]) -> dict[str, Any]:
        risks = await client.risks()
        cases = risks.get("cases", [])
        locks = [
            {"name": d.get("name"), "state": r.get("value")}
            for d in await client.devices()
            for c, r in (d.get("capabilities") or {}).items()
            if c == "lock.state"
        ]
        return {
            "open_risk_cases": len(cases),
            "confirmed": [c for c in cases if not c.get("advisory")],
            "locks": locks,
        }

    async def get_energy_summary(_: dict[str, Any]) -> dict[str, Any]:
        energy = await client.energy()
        buckets = energy.get("buckets", [])
        return {
            "buckets": len(buckets),
            "latest_watts": buckets[-1]["watts"] if buckets else None,
            # Hours with no reading are listed, not filled in with a zero.
            "missing_hours": len(energy.get("missing", [])),
        }

    async def _set_lock(args: dict[str, Any], locked: bool) -> dict[str, Any]:
        device_id, _c, name = await resolve(client, thing="قفل", room=args.get("room"))
        result = await client.set_capability(
            device_id, "lock.state", "locked" if locked else "unlocked"
        )
        return {"device": name, "locked": locked, "carried_out": _verified(result)}

    async def lock_door(args: dict[str, Any]) -> dict[str, Any]:
        return await _set_lock(args, True)

    async def unlock_door(args: dict[str, Any]) -> dict[str, Any]:
        return await _set_lock(args, False)

    def add(
        name: str,
        description: str,
        properties: dict[str, Any],
        required: list[str],
        run: Any,
        risk: RiskLevel = RiskLevel.LOW,
    ) -> None:
        registry.register(
            Tool(
                name=name,
                description=description,
                input_schema={
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
                output_schema={"type": "object"},
                risk=risk,
                run=run,
            )
        )

    room_arg = {"room": {**string, "description": "اسم الغرفة كما يقولها المستخدم"}}

    add("get_home_state", "حالة المنزل كاملة: الغرف والأجهزة وقراءاتها.", {}, [], get_home_state)
    add("get_room_state", "حالة غرفة واحدة وأجهزتها.", room_arg, ["room"], get_room_state)
    add(
        "list_available_devices",
        "الأجهزة المتاحة وما يمكن تشغيله منها.",
        {},
        [],
        list_available_devices,
    )
    add(
        "control_light",
        "تشغيل أو إطفاء إضاءة في غرفة.",
        {**room_arg, "on": {"type": "boolean"}, "thing": string},
        ["on"],
        control_light,
    )
    add(
        "set_light_brightness",
        "ضبط سطوع الإضاءة من صفر إلى مئة.",
        {**room_arg, "brightness": {"type": "integer"}},
        ["brightness"],
        set_light_brightness,
    )
    add(
        "set_ac_temperature",
        "ضبط درجة حرارة المكيّف بين ١٦ و٣٠.",
        {**room_arg, "temperature": {"type": "number"}},
        ["temperature"],
        set_ac_temperature,
    )
    add(
        "set_ac_mode",
        "تغيير وضع المكيّف: off, cool, heat, auto, dry, fan_only.",
        {**room_arg, "mode": string},
        ["mode"],
        set_ac_mode,
    )
    add(
        "control_curtain",
        "فتح أو إغلاق الستارة بنسبة من صفر إلى مئة.",
        {**room_arg, "position": {"type": "integer"}},
        ["position"],
        control_curtain,
    )
    add(
        "activate_scene",
        "تشغيل سيناريو منزلي بالاسم.",
        {"scene": string},
        ["scene"],
        activate_scene,
    )
    add(
        "get_sensor_state",
        "قراءة حسّاس: حرارة، رطوبة، حركة، غاز، تسرّب.",
        {"sensor": string},
        [],
        get_sensor_state,
    )
    add(
        "get_security_summary",
        "ملخّص الأمان: الأقفال والمخاطر المفتوحة.",
        {},
        [],
        get_security_summary,
    )
    add("get_energy_summary", "ملخّص استهلاك الطاقة.", {}, [], get_energy_summary)

    # Defined, and out of reach. `lock.state` is SECURITY_SENSITIVE, so both of
    # these are HIGH: the registry hides them from the model, and the
    # orchestrator refuses them, until the approval system of phase six exists.
    # They are written now so the gate has something real to refuse.
    add(
        "lock_door",
        "قفل باب.",
        {**room_arg},
        [],
        lock_door,
        risk=risk_for_safety_class("SECURITY_SENSITIVE"),
    )
    add(
        "unlock_door",
        "فتح قفل باب.",
        {**room_arg},
        [],
        unlock_door,
        risk=risk_for_safety_class("SECURITY_SENSITIVE"),
    )

    return registry
