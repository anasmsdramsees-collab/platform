from integrations.syltra.mock import FailingSyltraClient, MockSyltraClient
from tools.home import build_registry


async def test_turning_on_a_light_reaches_the_platform_not_home_assistant() -> None:
    client = MockSyltraClient()
    tool = build_registry(client).get("control_light")

    result = await tool.run({"room": "المجلس", "on": True})

    assert result["carried_out"] is True
    assert client.calls == [("set", ("light_majlis", "light.power", True))]


async def test_a_command_the_device_never_confirmed_is_not_reported_as_done() -> None:
    # §14.1. The hub accepted the command; the light never answered. Saying
    # "تم" here is the failure the whole verification field exists to prevent.
    tool = build_registry(FailingSyltraClient()).get("control_light")

    result = await tool.run({"room": "المجلس", "on": True})

    assert result["carried_out"] is False
    assert result["reason"]


async def test_an_impossible_temperature_is_refused_before_it_is_sent() -> None:
    client = MockSyltraClient()
    tool = build_registry(client).get("set_ac_temperature")

    from sella_core.errors import ToolError

    try:
        await tool.run({"room": "الصالة", "temperature": 45})
    except ToolError as error:
        assert error.code == "OUT_OF_RANGE"
    else:
        raise AssertionError("45 degrees should not have been accepted")

    assert client.calls == []


async def test_a_sensor_with_no_reading_is_reported_as_unknown() -> None:
    tool = build_registry(MockSyltraClient()).get("get_sensor_state")
    result = await tool.run({"sensor": "حرارة"})
    assert all("known" in s for s in result["sensors"])


async def test_a_scene_runs_by_its_arabic_name() -> None:
    client = MockSyltraClient()
    tool = build_registry(client).get("activate_scene")
    result = await tool.run({"scene": "وضع النوم"})
    assert result["carried_out"] is True
    assert client.calls[0][0] == "scene"


async def test_the_energy_summary_counts_the_hours_it_is_missing() -> None:
    tool = build_registry(MockSyltraClient()).get("get_energy_summary")
    result = await tool.run({})
    assert result["missing_hours"] == 0
    assert result["latest_watts"] == 1420.0
