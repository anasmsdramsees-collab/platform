"""Model registry: versions, promotion, rollback and suspension (spec §19).

The registry is where safety invariants 14 and 15 are enforced in code:

- A version arrives `TRAINED`. It only serves after ``promote()``, which is a
  deliberate, recorded act — **no model promotes itself**.
- Promotion refuses a version whose evaluation does not meet the registered
  gate for its model type, so "evaluated" means "evaluated *and passed*".
- ``rollback()`` restores the previous active version and records the reason,
  because a model that cannot be withdrawn is a model that cannot be trusted in
  a home.
- ``suspend()`` withdraws a version on drift, degradation or a safety event
  (spec §19.4) without needing a replacement ready.

Registries are per home (spec §14.4: per-home models); one household's model can
never serve another's.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from syltra_contracts import (
    ModelCard,
    ModelStatus,
    ModelType,
    ModelVersion,
    TrainingWindow,
)


class PromotionRefused(RuntimeError):
    """Raised when a version does not qualify to serve."""


class RollbackUnavailable(RuntimeError):
    """Raised when there is no prior version to fall back to."""


@dataclass(frozen=True)
class EvaluationGate:
    """The bar a version must clear before it may serve."""

    metric: str
    predicate: Callable[[float], bool]
    description: str

    def passes(self, metrics: dict[str, float]) -> bool:
        if self.metric not in metrics:
            return False
        return self.predicate(metrics[self.metric])


DEFAULT_GATES: dict[ModelType, EvaluationGate] = {
    # A comfort model that is more than 1.5 °C out is worse than the household's
    # own thermostat habits, so it must not serve.
    ModelType.TEMPERATURE_PREFERENCE: EvaluationGate(
        metric="mae",
        predicate=lambda v: v < 1.5,
        description="mean absolute error below 1.5 °C",
    ),
    # A routine model with no strong slot has found nothing worth acting on.
    ModelType.ROUTINE_BASELINE: EvaluationGate(
        metric="strong_buckets",
        predicate=lambda v: v >= 1.0,
        description="at least one established routine slot",
    ),
    # An anomaly model flagging a large share of its own training data is
    # miscalibrated and would bury the household in false positives.
    ModelType.ENERGY_ANOMALY: EvaluationGate(
        metric="flagged_fraction",
        predicate=lambda v: v <= 0.1,
        description="flags at most 10% of its training data",
    ),
}


@dataclass
class RegistryEvent:
    """An audit line for every lifecycle act (spec §25.5)."""

    occurred_at: datetime
    home_id: str
    action: str
    model_reference: str
    actor: str
    reason: str
    detail: dict[str, Any] = field(default_factory=dict)


class ModelRegistry:
    """In-memory registry of model versions per home.

    Persistence arrives with the model tables in a later phase; the lifecycle
    rules live here so they are identical whichever store backs them.
    """

    def __init__(self, gates: dict[ModelType, EvaluationGate] | None = None) -> None:
        self._versions: dict[str, list[ModelVersion]] = {}
        self._gates = dict(gates if gates is not None else DEFAULT_GATES)
        self.audit: list[RegistryEvent] = []

    # ── registration ──

    def register(
        self,
        home_id: str,
        name: str,
        version: str,
        model_type: ModelType,
        feature_schema_version: str,
        training_code_revision: str,
        training_window: TrainingWindow,
        evaluation_metrics: dict[str, float],
        card: ModelCard,
        artifact_path: str | None = None,
        artifact_sha256: str | None = None,
        calibration: dict[str, float] | None = None,
    ) -> ModelVersion:
        """Record a newly trained version. It does not serve yet."""
        record = ModelVersion(
            model_id=uuid4(),
            home_id=home_id,
            name=name,
            version=version,
            model_type=model_type,
            feature_schema_version=feature_schema_version,
            training_code_revision=training_code_revision,
            training_window=training_window,
            evaluation_metrics=evaluation_metrics,
            calibration=calibration or {},
            created_at=datetime.now(tz=UTC),
            status=ModelStatus.TRAINED,
            artifact_path=artifact_path,
            artifact_sha256=artifact_sha256,
            card=card,
            rollback_target=self._active_reference(home_id, name),
        )
        self._versions.setdefault(home_id, []).append(record)
        self._record(home_id, "MODEL_REGISTERED", record.reference, "adaptive-engine",
                     "training completed", {"metrics": evaluation_metrics})
        return record

    # ── queries ──

    def versions(self, home_id: str, name: str | None = None) -> list[ModelVersion]:
        found = self._versions.get(home_id, [])
        if name is not None:
            found = [v for v in found if v.name == name]
        return sorted(found, key=lambda v: v.created_at)

    def active(self, home_id: str, name: str) -> ModelVersion | None:
        for record in reversed(self.versions(home_id, name)):
            if record.status is ModelStatus.ACTIVE:
                return record
        return None

    def get(self, home_id: str, name: str, version: str) -> ModelVersion | None:
        return next(
            (v for v in self.versions(home_id, name) if v.version == version), None
        )

    def gate_for(self, model_type: ModelType) -> EvaluationGate | None:
        return self._gates.get(model_type)

    # ── lifecycle ──

    def promote(
        self, home_id: str, name: str, version: str, actor: str = "operator"
    ) -> ModelVersion:
        """Promote a version to serve. Refuses if evaluation does not qualify."""
        record = self.get(home_id, name, version)
        if record is None:
            msg = f"no version {name}@{version} registered for {home_id}"
            raise PromotionRefused(msg)
        if record.status is ModelStatus.ACTIVE:
            return record

        gate = self._gates.get(record.model_type)
        if gate is not None and not gate.passes(record.evaluation_metrics):
            observed = record.evaluation_metrics.get(gate.metric, "absent")
            msg = (
                f"{record.reference} does not meet the promotion gate "
                f"({gate.description}); {gate.metric}={observed}"
            )
            self._record(home_id, "MODEL_PROMOTION_REFUSED", record.reference, actor, msg)
            raise PromotionRefused(msg)

        previous = self.active(home_id, name)
        promoted = record.model_copy(
            update={
                "status": ModelStatus.ACTIVE,
                "promoted_at": datetime.now(tz=UTC),
                "rollback_target": previous.version if previous else None,
            }
        )
        self._replace(home_id, promoted)
        if previous is not None:
            self._replace(
                home_id, previous.model_copy(update={"status": ModelStatus.ROLLED_BACK})
            )
        self._record(
            home_id, "MODEL_ACTIVATED", promoted.reference, actor, "promotion approved",
            {"previous": previous.reference if previous else None},
        )
        return promoted

    def rollback(
        self, home_id: str, name: str, actor: str = "operator", reason: str = "manual rollback"
    ) -> ModelVersion:
        """Return service to the previous version."""
        current = self.active(home_id, name)
        if current is None:
            msg = f"{name} has no active version for {home_id} to roll back from"
            raise RollbackUnavailable(msg)
        if current.rollback_target is None:
            msg = f"{current.reference} records no rollback target"
            raise RollbackUnavailable(msg)
        target = self.get(home_id, name, current.rollback_target)
        if target is None:
            msg = f"rollback target {name}@{current.rollback_target} is no longer registered"
            raise RollbackUnavailable(msg)

        self._replace(home_id, current.model_copy(update={"status": ModelStatus.ROLLED_BACK}))
        restored = target.model_copy(
            update={"status": ModelStatus.ACTIVE, "promoted_at": datetime.now(tz=UTC)}
        )
        self._replace(home_id, restored)
        self._record(
            home_id, "MODEL_ROLLED_BACK", restored.reference, actor, reason,
            {"from": current.reference},
        )
        return restored

    def suspend(
        self, home_id: str, name: str, reason: str, actor: str = "adaptive-engine"
    ) -> ModelVersion:
        """Withdraw the active version (spec §19.4 drift and degradation)."""
        current = self.active(home_id, name)
        if current is None:
            msg = f"{name} has no active version for {home_id} to suspend"
            raise RollbackUnavailable(msg)
        suspended = current.model_copy(update={"status": ModelStatus.SUSPENDED})
        self._replace(home_id, suspended)
        self._record(home_id, "MODEL_SUSPENDED", suspended.reference, actor, reason)
        return suspended

    # ── internals ──

    def _active_reference(self, home_id: str, name: str) -> str | None:
        current = self.active(home_id, name)
        return current.version if current else None

    def _replace(self, home_id: str, record: ModelVersion) -> None:
        versions = self._versions.setdefault(home_id, [])
        for index, existing in enumerate(versions):
            if existing.model_id == record.model_id:
                versions[index] = record
                return
        versions.append(record)

    def _record(
        self,
        home_id: str,
        action: str,
        reference: str,
        actor: str,
        reason: str,
        detail: dict[str, Any] | None = None,
    ) -> None:
        self.audit.append(
            RegistryEvent(
                occurred_at=datetime.now(tz=UTC),
                home_id=home_id,
                action=action,
                model_reference=reference,
                actor=actor,
                reason=reason,
                detail=detail or {},
            )
        )


def build_card(
    model_type: ModelType,
    summary: str,
    limitations: str,
    training_data: str,
    evaluation: str,
) -> ModelCard:
    """Model card with the safety language every SYLTRA model shares."""
    return ModelCard(
        summary=summary,
        intended_use=(
            "Produce advisory recommendations for review by the Policy and Safety "
            "Service. Output is never an actuator command."
        ),
        out_of_scope_use=(
            "Any life-safety decision, emergency response, or direct control of "
            "locks, valves, breakers, sirens or garage doors. Confirmed emergency "
            "response is deterministic and rule-based (safety invariants 6 and 18)."
        ),
        training_data=training_data,
        evaluation=evaluation,
        limitations=limitations,
        ethical_and_safety_notes=(
            "Trained per household on local data that never leaves the hub. "
            "Cannot raise its own permission level; cannot serve without explicit "
            "promotion; suspended automatically on drift or sensor degradation."
        ),
    )
