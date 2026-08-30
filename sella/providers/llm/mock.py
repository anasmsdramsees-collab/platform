"""A model that does not need a key.

It is not an imitation of Claude. It is a scripted caller: it reads the last
user message, picks the tool a person would obviously have meant, and returns a
short Arabic sentence. That is enough to prove the loop, the permissions, the
audit trail and the honesty rules without spending a token or needing a network.
"""

import re
from typing import Any

from providers.llm.base import LLMProvider, LLMReply, ToolCall
from tools.home import capability_from_words, room_from_words


def _digits(text: str) -> int | None:
    arabic = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
    found = re.search(r"\d+", text.translate(arabic))
    return int(found.group()) if found else None


class MockLLM(LLMProvider):
    def __init__(self) -> None:
        self.seen: list[str] = []

    async def reply(
        self, system: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> LLMReply:
        available = {t["name"] for t in tools}

        # A tool result has come back: say what happened, in one line.
        last = messages[-1] if messages else {}
        if last.get("role") == "tool":
            payload = last.get("content", {})
            if isinstance(payload, dict) and payload.get("error"):
                return LLMReply(text=str(payload.get("spoken", "ما نفع.")))
            if isinstance(payload, dict) and payload.get("carried_out") is False:
                return LLMReply(text="أرسلت الأمر لكن الجهاز ما أكّد. تحقّق منه.")
            return LLMReply(text="تم.")

        text = str(last.get("content", ""))
        self.seen.append(text)
        room = room_from_words(text)
        capability = capability_from_words(text)
        number = _digits(text)

        def call(name: str, **args: Any) -> LLMReply:
            return LLMReply(
                tool_calls=(ToolCall(id=f"call_{len(self.seen)}", name=name, arguments=args),)
            )

        if "سيناريو" in text or "وضع" in text:
            scene = text.split("وضع", 1)[-1].strip() if "وضع" in text else text
            if "activate_scene" in available:
                return call("activate_scene", scene=f"وضع {scene}".strip())
        if capability == "climate.target_temperature" and number is not None:
            return call("set_ac_temperature", temperature=float(number), room=room)
        if capability == "cover.position" and "control_curtain" in available:
            position = number if number is not None else (100 if "افتح" in text else 0)
            return call("control_curtain", position=position, room=room)
        if capability == "light.power":
            if number is not None and "سطوع" in text:
                return call("set_light_brightness", brightness=number, room=room)
            on = not any(w in text for w in ("طفي", "اطفي", "أطفئ", "اقفل", "سكر"))
            return call("control_light", on=on, room=room, thing="إضاءة")
        if capability == "lock.state":
            return call("unlock_door", room=room)
        if any(w in text for w in ("غاز", "حسّاس", "حساس", "حرارة", "رطوبة")):
            return call("get_sensor_state", sensor=text)
        if "أمان" in text or "امان" in text or "قفل" in text:
            return call("get_security_summary")
        if "طاقة" in text or "كهرب" in text:
            return call("get_energy_summary")
        if "غرفة" in text or room:
            return call("get_room_state", room=room or text)
        return call("get_home_state")
