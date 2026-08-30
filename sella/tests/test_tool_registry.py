from typing import Any

import pytest

from integrations.syltra.mock import MockSyltraClient
from policies.risk import RiskLevel
from sella_core.errors import ToolError
from tools.home import build_registry
from tools.registry import Tool, ToolRegistry


async def _noop(_: dict[str, Any]) -> dict[str, Any]:
    return {}


def _tool(name: str, risk: RiskLevel) -> Tool:
    return Tool(
        name=name,
        description=name,
        input_schema={"type": "object"},
        output_schema={"type": "object"},
        risk=risk,
        run=_noop,
    )


def test_the_twelve_phase_one_tools_are_registered() -> None:
    names = set(build_registry(MockSyltraClient()).names())
    expected = {
        "get_home_state",
        "get_room_state",
        "list_available_devices",
        "control_light",
        "set_light_brightness",
        "set_ac_temperature",
        "set_ac_mode",
        "control_curtain",
        "activate_scene",
        "get_sensor_state",
        "get_security_summary",
        "get_energy_summary",
    }
    assert expected <= names


def test_the_model_never_sees_a_door() -> None:
    registry = build_registry(MockSyltraClient())
    shown = {t["name"] for t in registry.exposed_to_model(high_risk_enabled=False)}
    assert "unlock_door" not in shown
    assert "lock_door" not in shown
    assert "control_light" in shown


def test_a_forbidden_tool_is_hidden_even_when_high_risk_is_enabled() -> None:
    registry = ToolRegistry()
    registry.register(_tool("open_gas_valve", RiskLevel.FORBIDDEN))
    registry.register(_tool("unlock", RiskLevel.HIGH))
    shown = {t["name"] for t in registry.exposed_to_model(high_risk_enabled=True)}
    assert shown == {"unlock"}


def test_asking_for_a_tool_that_does_not_exist_is_an_error_not_a_shrug() -> None:
    with pytest.raises(ToolError) as caught:
        ToolRegistry().get("delete_house")
    assert caught.value.code == "UNKNOWN_TOOL"
