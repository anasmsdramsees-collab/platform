"""JSON Schema export (spec §11.3: store JSON Schema for every event).

Schemas are generated from the Pydantic models so they cannot drift from the
code that validates at runtime. ``contracts/jsonschema/`` holds the checked-in
copies; ``make contracts`` regenerates them and a contract test fails the build
if the checked-in files no longer match the models.

Files are written under a schema-version directory so older consumers keep a
stable reference when the envelope version advances.
"""

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from syltra_contracts.capability_definitions import CAPABILITY_DEFINITIONS
from syltra_contracts.contexts import ContextRecord, EvidenceItem
from syltra_contracts.actions import ActionRequest, ActionResult
from syltra_contracts.deadletter import DeadLetterRecord
from syltra_contracts.feedback import FeedbackRecord
from syltra_contracts.policy import PolicyDecision
from syltra_contracts.risk import RiskCase, RiskEvidenceItem
from syltra_contracts.models_registry import ModelCard, ModelVersion
from syltra_contracts.recommendations import Recommendation
from syltra_contracts.events import EVENT_TYPES, SCHEMA_VERSION, EventEnvelope
from syltra_contracts.gateway import (
    CapabilityCommand,
    DeviceInfo,
    EntityInfo,
    EntityState,
    RegistrySnapshot,
)

_MODELS: dict[str, type[BaseModel]] = {
    "event-envelope": EventEnvelope,
    "deadletter-record": DeadLetterRecord,
    "context-record": ContextRecord,
    "recommendation": Recommendation,
    "policy-decision": PolicyDecision,
    "action-request": ActionRequest,
    "action-result": ActionResult,
    "feedback-record": FeedbackRecord,
    "risk-case": RiskCase,
    "risk-evidence-item": RiskEvidenceItem,
    "model-version": ModelVersion,
    "model-card": ModelCard,
    "evidence-item": EvidenceItem,
    "capability-command": CapabilityCommand,
    "device-info": DeviceInfo,
    "entity-info": EntityInfo,
    "entity-state": EntityState,
    "registry-snapshot": RegistrySnapshot,
}


def _identifier(name: str) -> str:
    return f"https://contracts.syltra.local/{SCHEMA_VERSION}/{name}.schema.json"


def build_schemas() -> dict[str, dict[str, Any]]:
    """Return every contract schema keyed by file stem."""
    schemas: dict[str, dict[str, Any]] = {}
    for name, model in _MODELS.items():
        schema = model.model_json_schema(mode="serialization")
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        schema["$id"] = _identifier(name)
        schemas[name] = schema

    # A machine-readable registry of the closed vocabularies, so non-Python
    # consumers can validate event types and capability domains too.
    schemas["event-types"] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": _identifier("event-types"),
        "title": "SYLTRA event types",
        "description": "Closed set of event types (spec §11.2).",
        "type": "string",
        "enum": sorted(EVENT_TYPES),
    }
    schemas["capability-registry"] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": _identifier("capability-registry"),
        "title": "SYLTRA capability registry",
        "description": "Canonical capabilities and their declared properties (spec §10).",
        "type": "object",
        "properties": {
            capability: {
                "type": "object",
                "const": {
                    "data_type": definition.data_type.value,
                    "access": definition.access.value,
                    "safety_class": definition.safety_class.value,
                    "freshness_seconds": definition.freshness_seconds,
                    "reversible": definition.reversible,
                    "confirmation": definition.confirmation.value,
                    "unit": definition.unit,
                    "minimum": definition.minimum,
                    "maximum": definition.maximum,
                    "allowed_values": list(definition.allowed_values),
                },
            }
            for capability, definition in sorted(CAPABILITY_DEFINITIONS.items())
        },
    }
    return schemas


def schema_directory(root: Path) -> Path:
    return root / "contracts" / "jsonschema" / f"v{SCHEMA_VERSION}"


def write_schemas(root: Path) -> list[Path]:
    """Write all schemas under ``root``; returns the paths written."""
    target = schema_directory(root)
    target.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, schema in build_schemas().items():
        path = target / f"{name}.schema.json"
        path.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written.append(path)
    return written


def main() -> None:  # pragma: no cover - thin CLI wrapper
    root = Path(__file__).resolve().parents[4]
    for path in write_schemas(root):
        print(f"wrote {path.relative_to(root)}")


if __name__ == "__main__":  # pragma: no cover
    main()
