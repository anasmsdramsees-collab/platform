"""Turning what a person said into one device, or refusing to guess."""

import pytest

from integrations.syltra.mock import MockSyltraClient
from sella_core.errors import ToolError
from tools.home import capability_from_words, resolve, room_from_words


def test_spelling_a_word_differently_still_finds_the_thing() -> None:
    # "مكيّف" with a shadda and "مكيف" without it are the same request.
    assert capability_from_words("شغّل المكيّف") == "climate.target_temperature"
    assert capability_from_words("شغل المكيف") == "climate.target_temperature"


def test_a_household_word_for_a_room_is_understood() -> None:
    assert room_from_words("في المجلس") == "majlis"
    assert room_from_words("غرفة المعيشة") == "living_room"


async def test_two_candidates_and_no_room_is_a_question_not_a_coin_toss() -> None:
    with pytest.raises(ToolError) as caught:
        await resolve(MockSyltraClient(), thing="إضاءة")
    assert caught.value.code == "AMBIGUOUS_DEVICE"
    # The refusal must be sayable out loud.
    assert "أي وحدة" in caught.value.spoken


async def test_naming_the_room_settles_it() -> None:
    device_id, capability, _name = await resolve(MockSyltraClient(), thing="إضاءة", room="المجلس")
    assert device_id == "light_majlis"
    assert capability == "light.power"


async def test_a_room_with_no_such_device_says_so() -> None:
    with pytest.raises(ToolError) as caught:
        await resolve(MockSyltraClient(), thing="ستارة", room="المطبخ")
    assert caught.value.code == "NO_SUCH_DEVICE"
