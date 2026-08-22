"""The worked examples must stay valid, current, and cross-referenced.

An example that a schema change silently invalidated is worse than no example:
an integrator builds against it and finds out from a runtime rejection.
"""

import json
from pathlib import Path
from typing import Any

import pytest
from syltra_contracts.example_export import (
    ACTION_ID,
    CORRELATION_ID,
    DECISION_ID,
    HOME,
    IDEMPOTENCY_KEY,
    RECOMMENDATION_ID,
    build_examples,
    examples_directory,
    write_examples,
)
from syltra_contracts.schema_export import _MODELS

pytestmark = pytest.mark.contract

ROOT = Path(__file__).resolve().parents[3]


def _checked_in(name: str) -> dict[str, Any]:
    path = examples_directory(ROOT) / f"{name}.example.json"
    assert path.exists(), f"{path} is missing; run 'make examples'"
    document: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return document


def test_every_contract_has_a_worked_example() -> None:
    missing = set(_MODELS) - set(build_examples())
    assert not missing, f"contracts with a schema but no example: {sorted(missing)}"


def test_no_example_describes_a_contract_that_no_longer_exists() -> None:
    orphaned = set(build_examples()) - set(_MODELS)
    assert not orphaned, f"examples for unknown contracts: {sorted(orphaned)}"


@pytest.mark.parametrize("name", sorted(build_examples()))
def test_each_example_revalidates_through_its_model(name: str) -> None:
    """The document on disk is one the runtime would accept."""
    _MODELS[name].model_validate(_checked_in(name))


@pytest.mark.parametrize("name", sorted(build_examples()))
def test_each_checked_in_example_is_current(name: str) -> None:
    assert _checked_in(name) == build_examples()[name].model_dump(mode="json"), (
        f"{name} is stale; run 'make examples'"
    )


def test_regeneration_is_deterministic(tmp_path: Path) -> None:
    """Fixed timestamps and ids, so `make examples` produces no spurious diff."""
    first = {p.name: p.read_text(encoding="utf-8") for p in write_examples(tmp_path)}
    second = {p.name: p.read_text(encoding="utf-8") for p in write_examples(tmp_path)}
    assert first == second


def test_the_examples_reference_each_other() -> None:
    """The whole point: following an id across documents has to work.

    Twenty independently-plausible documents would each pass validation and
    still teach nobody how the pipeline hangs together.
    """
    recommendation = _checked_in("recommendation")
    decision = _checked_in("policy-decision")
    request = _checked_in("action-request")
    result = _checked_in("action-result")
    feedback = _checked_in("feedback-record")

    assert decision["recommendation_id"] == recommendation["recommendation_id"]
    assert feedback["recommendation_id"] == recommendation["recommendation_id"]
    assert request["decision_id"] == decision["decision_id"] == str(DECISION_ID)
    assert result["action_id"] == request["action_id"] == str(ACTION_ID)
    assert result["idempotency_key"] == request["idempotency_key"] == IDEMPOTENCY_KEY
    assert result["correlation_id"] == request["correlation_id"] == str(CORRELATION_ID)
    assert recommendation["recommendation_id"] == str(RECOMMENDATION_ID)


def test_the_action_carries_out_what_the_recommendation_proposed() -> None:
    recommendation = _checked_in("recommendation")
    request = _checked_in("action-request")
    result = _checked_in("action-result")

    assert request["target"]["device_id"] == recommendation["target"]["device_id"]
    assert request["target"]["capability"] == recommendation["target"]["capability"]
    assert request["value"] == recommendation["proposed_value"]
    assert result["observed_value"] == request["value"], (
        "the example should verify, not just claim"
    )


def test_every_example_belongs_to_the_same_synthetic_home() -> None:
    """Spec §0 rule 15: synthetic data only, and one home so the story holds."""
    for name, document in ((n, _checked_in(n)) for n in build_examples()):
        if "home_id" in document:
            assert document["home_id"] == HOME, f"{name} belongs to another home"
