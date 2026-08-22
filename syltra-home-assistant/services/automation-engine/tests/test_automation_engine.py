"""Automation engine tests (spec §2.3, invariants 2, 5 and 7, ADR-009).

This is the first component in the platform a household authors itself, and the
first that can move a device without anyone approving that particular move. The
tests are organised around what must remain true of it rather than around its
methods.
"""

import subprocess
import sys
from datetime import UTC, datetime, timedelta

import pytest
from syltra_automation_engine import ECHO_WINDOW, AutomationEngine, SkipReason
from syltra_contracts import (
    Automation,
    AutomationAction,
    AutomationCondition,
    AutomationTrigger,
    ConditionKind,
    TriggerKind,
)
from syltra_digital_twin.core import HomeState
from syltra_testing import build_device as device
from syltra_testing import build_home as home
from syltra_testing import build_reading as reading

NOW = datetime(2026, 8, 20, 19, 30, tzinfo=UTC)
HOME = "home_001"


def lights_on_when_motion(**overrides: object) -> Automation:
    fields = {
        "home_id": HOME,
        "name": "Hall light on motion",
        "trigger": AutomationTrigger(
            kind=TriggerKind.STATE_EQUALS,
            capability="occupancy.motion",
            device_id="motion_hall",
            value=True,
        ),
        "actions": (
            AutomationAction(capability="light.power", value=True, device_id="light_hall"),
        ),
    }
    fields.update(overrides)
    return Automation(**fields)


def hall(motion: bool = True, light: bool = False, at: datetime = NOW) -> HomeState:
    return home(
        device("motion_hall", "hall", m=reading("occupancy.motion", motion, at)),
        device("light_hall", "hall", p=reading("light.power", light, at)),
        home_id=HOME,
    )


# ── invariant 7: fixed automations survive the Adaptive Engine ──


@pytest.mark.safety
def test_the_engine_imports_without_any_ml_package() -> None:
    # Invariant 7: loss of the Adaptive Engine does not stop fixed automations.
    # A fresh interpreter, so another test's imports cannot mask the answer.
    code = (
        "import sys, syltra_automation_engine;"
        "bad=[m for m in ('sklearn','onnxruntime','skl2onnx','polars',"
        "'syltra_adaptive_engine') if m in sys.modules];"
        "print(bad)"
    )
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    assert result.stdout.strip() == "[]", result.stdout


@pytest.mark.safety
def test_an_automation_runs_with_no_adaptive_engine_present() -> None:
    # The other half of invariant 7, which previously had nothing to test on:
    # the test named for it exercised only the Safety Governor.
    engine = AutomationEngine()
    engine.upsert(lights_on_when_motion())
    result = engine.evaluate(HOME, hall(), NOW)
    assert len(result.proposals) == 1
    assert result.proposals[0].action.capability == "light.power"


# ── invariant 2: an automation is not a way past policy ──


@pytest.mark.safety
def test_the_engine_cannot_dispatch() -> None:
    # It proposes. Policy decides. The engine holds nothing that could send.
    engine = AutomationEngine()
    for forbidden in ("execute", "dispatch", "send", "gateway", "orchestrator", "publish"):
        assert not hasattr(engine, forbidden), forbidden
    for attribute in vars(engine):
        assert "gateway" not in attribute.lower()
        assert "client" not in attribute.lower()


@pytest.mark.safety
def test_a_proposal_carries_no_result_field() -> None:
    # Shaped like a recommendation, not an action: there is no field that could
    # record a dispatch, so nothing can pretend one happened here.
    engine = AutomationEngine()
    engine.upsert(lights_on_when_motion())
    proposal = engine.evaluate(HOME, hall(), NOW).proposals[0]
    for forbidden in ("status", "result", "dispatched", "observed_value"):
        assert not hasattr(proposal, forbidden), forbidden


@pytest.mark.safety
def test_a_proposal_expires() -> None:
    # §0: every action is time-bounded. A proposal that sat pending through a
    # change of circumstances must not run against the home that exists now.
    engine = AutomationEngine()
    engine.upsert(lights_on_when_motion())
    proposal = engine.evaluate(HOME, hall(), NOW).proposals[0]
    assert proposal.expires_at > NOW
    assert not proposal.is_expired_at(NOW)
    assert proposal.is_expired_at(proposal.expires_at)


# ── §2.3: non-critical only ──


@pytest.mark.safety
@pytest.mark.parametrize(
    "capability", ["lock.state", "valve.state", "siren.state", "breaker.state", "garage.state"]
)
def test_an_automation_cannot_be_built_that_touches_a_critical_capability(
    capability: str,
) -> None:
    # Refused at construction, not at dispatch. Such an automation should not
    # exist as an object to be stored, listed or reasoned about.
    with pytest.raises(ValueError, match="automations may only act on"):
        AutomationAction(capability=capability, value="x", device_id="d")


@pytest.mark.safety
def test_an_automation_cannot_set_a_read_only_capability() -> None:
    # Chosen so the read-only rule is what fires: a life-safety capability
    # would be refused by the safety-class check first, and this test would
    # then be proving the wrong thing.
    from syltra_contracts.automations import AUTOMATABLE_SAFETY_CLASSES
    from syltra_contracts.capability_definitions import get_definition

    definition = get_definition("environment.temperature")
    assert definition.safety_class in AUTOMATABLE_SAFETY_CLASSES
    assert definition.access.value == "READ"

    with pytest.raises(ValueError, match="read-only"):
        AutomationAction(capability="environment.temperature", value=21.0, device_id="d")


# ── invariant 5 / §0 rule 16: a person's hand wins ──


@pytest.mark.safety
def test_a_manual_change_stops_the_automation_that_would_undo_it() -> None:
    engine = AutomationEngine()
    engine.upsert(lights_on_when_motion())
    just_now = {("light_hall", "light.power"): NOW - timedelta(seconds=5)}
    result = engine.evaluate(HOME, hall(), NOW, manual_override=just_now)
    assert not result.proposals
    assert result.reason_for(engine.list_for(HOME)[0].automation_id) == SkipReason.MANUAL_OVERRIDE


@pytest.mark.safety
def test_the_manual_override_lapses_so_automation_resumes() -> None:
    # A person's choice wins for a while, not for ever — otherwise one manual
    # change would silently disable an automation the household still wants.
    engine = AutomationEngine()
    engine.upsert(lights_on_when_motion())
    long_ago = {("light_hall", "light.power"): NOW - ECHO_WINDOW - timedelta(seconds=1)}
    assert engine.evaluate(HOME, hall(), NOW, manual_override=long_ago).proposals


# ── §14.8: no feedback loops ──


@pytest.mark.safety
def test_an_automation_does_not_fire_on_its_own_echo() -> None:
    # It turns the light on; the light reports it is on; that is not a reason
    # to turn it on again.
    engine = AutomationEngine()
    engine.upsert(
        lights_on_when_motion(
            trigger=AutomationTrigger(
                kind=TriggerKind.STATE_EQUALS,
                capability="light.power",
                device_id="light_hall",
                value=True,
            ),
            rearm_seconds=30,
        )
    )
    first = engine.evaluate(HOME, hall(light=True), NOW)
    assert first.proposals

    # Well past the rearm interval, but the light still reads what we set.
    later = NOW + timedelta(seconds=45)
    second = engine.evaluate(HOME, hall(light=True, at=later), later)
    assert not second.proposals
    assert second.reason_for(engine.list_for(HOME)[0].automation_id) == SkipReason.OWN_ECHO


@pytest.mark.safety
def test_an_automation_cannot_fire_faster_than_its_rearm_interval() -> None:
    # The bound that catches any loop the echo check misses, including one that
    # runs through a second automation.
    engine = AutomationEngine()
    engine.upsert(lights_on_when_motion(rearm_seconds=60))
    assert engine.evaluate(HOME, hall(), NOW).proposals
    soon = NOW + timedelta(seconds=30)
    result = engine.evaluate(HOME, hall(at=soon), soon)
    assert not result.proposals
    assert result.reason_for(engine.list_for(HOME)[0].automation_id) == SkipReason.REARMING


@pytest.mark.safety
def test_the_rearm_floor_cannot_be_set_away() -> None:
    with pytest.raises(ValueError, match="rearm_seconds must be at least"):
        lights_on_when_motion(rearm_seconds=1)


# ── ordinary behaviour ──


def test_a_disabled_automation_never_fires() -> None:
    engine = AutomationEngine()
    engine.upsert(lights_on_when_motion(enabled=False))
    result = engine.evaluate(HOME, hall(), NOW)
    assert not result.proposals
    assert result.reason_for(engine.list_for(HOME)[0].automation_id) == SkipReason.DISABLED


def test_disabling_keeps_the_automation_rather_than_deleting_it() -> None:
    engine = AutomationEngine()
    created = engine.upsert(lights_on_when_motion())
    engine.set_enabled(HOME, created.automation_id, False)
    stored = engine.get(HOME, created.automation_id)
    assert stored is not None and stored.enabled is False
    assert stored.version == created.version + 1


def test_a_condition_that_does_not_hold_stops_the_automation() -> None:
    engine = AutomationEngine()
    engine.upsert(
        lights_on_when_motion(
            conditions=(
                AutomationCondition(
                    kind=ConditionKind.CONTEXT_ACTIVE, context_type="HOME_OCCUPIED"
                ),
            )
        )
    )
    result = engine.evaluate(HOME, hall(), NOW, active_contexts=())
    assert not result.proposals
    assert (
        result.reason_for(engine.list_for(HOME)[0].automation_id) == SkipReason.CONDITION_NOT_MET
    )
    assert engine.evaluate(HOME, hall(), NOW, active_contexts=("HOME_OCCUPIED",)).proposals


@pytest.mark.safety
def test_a_condition_over_an_unknown_value_is_not_satisfied() -> None:
    # Unknown is treated as false in the direction that does not act. An
    # automation should not fire because the platform cannot see a reason not
    # to.
    engine = AutomationEngine()
    engine.upsert(
        lights_on_when_motion(
            conditions=(
                AutomationCondition(
                    kind=ConditionKind.THRESHOLD_BELOW,
                    capability="environment.temperature",
                    value=20,
                ),
            )
        )
    )
    assert not engine.evaluate(HOME, hall(), NOW).proposals


def test_a_dry_run_proposes_without_recording_that_it_fired() -> None:
    # What test mode in the console needs, and what makes offering one safe.
    engine = AutomationEngine()
    created = engine.upsert(lights_on_when_motion())
    assert engine.evaluate(HOME, hall(), NOW, dry_run=True).proposals
    assert engine.last_fired(HOME, created.automation_id) is None
    # And the real run is still available immediately afterwards.
    assert engine.evaluate(HOME, hall(), NOW).proposals
    assert engine.last_fired(HOME, created.automation_id) == NOW


def test_homes_are_isolated() -> None:
    engine = AutomationEngine()
    engine.upsert(lights_on_when_motion())
    assert engine.list_for("home_other") == []
    assert not engine.evaluate("home_other", hall(), NOW).proposals


def test_a_threshold_trigger_fires_on_the_right_side() -> None:
    engine = AutomationEngine()
    engine.upsert(
        lights_on_when_motion(
            name="Cool when warm",
            trigger=AutomationTrigger(
                kind=TriggerKind.THRESHOLD_ABOVE,
                capability="environment.temperature",
                device_id="t1",
                value=26,
            ),
            actions=(
                AutomationAction(
                    capability="climate.target_temperature", value=23.0, device_id="ac"
                ),
            ),
        )
    )
    warm = home(
        device("t1", "living_room", t=reading("environment.temperature", 27.4, NOW, "C")),
        home_id=HOME,
    )
    cool = home(
        device("t1", "living_room", t=reading("environment.temperature", 22.0, NOW, "C")),
        home_id=HOME,
    )
    assert engine.evaluate(HOME, warm, NOW).proposals
    assert not engine.evaluate(HOME, cool, NOW).proposals


def test_the_summary_reads_as_a_sentence_a_person_can_check() -> None:
    # §17.8 asks for a readable summary before save.
    summary = lights_on_when_motion().summary()
    assert "light_hall:light.power=True" in summary
