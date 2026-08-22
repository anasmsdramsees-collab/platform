"""JSON Schema export tests (spec §11.3).

The checked-in schemas in ``contracts/jsonschema/`` are the interface other
languages and services validate against. If they drift from the Pydantic models
that validate at runtime, two consumers can disagree about what is valid — so
drift fails the build here rather than in production.
"""

import json
from pathlib import Path

import pytest
from syltra_contracts.events import EVENT_TYPES, SCHEMA_VERSION
from syltra_contracts.schema_export import build_schemas, schema_directory

pytestmark = pytest.mark.contract

# libs/contracts/tests/<this file> → repo root
REPO_ROOT = Path(__file__).resolve().parents[3]


def test_schema_files_are_checked_in() -> None:
    directory = schema_directory(REPO_ROOT)
    assert directory.is_dir(), f"missing {directory}; run 'make contracts'"
    for name in build_schemas():
        assert (directory / f"{name}.schema.json").is_file(), f"missing schema for {name}"


def test_checked_in_schemas_match_the_models() -> None:
    directory = schema_directory(REPO_ROOT)
    for name, expected in build_schemas().items():
        path = directory / f"{name}.schema.json"
        actual = json.loads(path.read_text(encoding="utf-8"))
        assert actual == expected, (
            f"{path.name} is out of date with the Pydantic models — run 'make contracts'"
        )


def test_schemas_are_versioned_and_identified() -> None:
    for name, schema in build_schemas().items():
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["$id"].endswith(f"/{SCHEMA_VERSION}/{name}.schema.json")


def test_envelope_schema_requires_the_identity_fields() -> None:
    envelope = build_schemas()["event-envelope"]
    required = set(envelope["required"])
    for field in (
        "event_id",
        "event_type",
        "schema_version",
        "occurred_at",
        "received_at",
        "home_id",
        "correlation_id",
        "source",
    ):
        assert field in required


def test_event_types_schema_lists_every_contract_type() -> None:
    assert set(build_schemas()["event-types"]["enum"]) == EVENT_TYPES


def test_capability_registry_schema_publishes_safety_attributes() -> None:
    registry = build_schemas()["capability-registry"]["properties"]
    gas_valve = registry["valve.state"]["const"]
    assert gas_valve["safety_class"] == "LIFE_SAFETY_CRITICAL"
    assert gas_valve["confirmation"] == "DETERMINISTIC_SAFETY_RULE"
    temperature = registry["environment.temperature"]["const"]
    assert temperature["unit"] == "C"
    assert temperature["freshness_seconds"] > 0
