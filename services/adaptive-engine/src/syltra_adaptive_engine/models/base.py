"""Shared model scaffolding (spec §14.4, §19.3).

Every baseline model implements the same small contract:

- ``requirement`` — the minimum data it needs before training may begin;
- ``train`` — deterministic given the same frame, returning a ``TrainingResult``
  that either holds a fitted model **or** explains why it refused;
- ``predict`` — validated output, never a bare float the caller must trust.

A model never returns a recommendation. It returns a prediction; the engine
decides whether that prediction is worth proposing, and the proposal is still
only advisory (safety invariant 1).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import polars as pl

from syltra_adaptive_engine.features import DataRequirement, DataSufficiency
from syltra_contracts import ModelType


@dataclass(frozen=True)
class Prediction:
    """A model output with its own confidence and explanation."""

    value: Any
    confidence: float
    reason_codes: list[str] = field(default_factory=list)
    detail: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            msg = f"prediction confidence {self.confidence} is outside [0, 1]"
            raise ValueError(msg)


class InsufficientCapabilityData(Exception):
    """A model's own capability is under-represented in an otherwise ample frame.

    The global data requirement counts every event in the home, so a frame can
    hold thousands of rows and still contain nothing a particular model can
    learn from — plenty of light switches, no power readings. Raising from
    ``_fit`` routes that through the same refusal path as sparse data, instead
    of leaving a model that reports itself trained but has no parameters.
    """

    def __init__(self, reason_code: str, observed: int, required: int) -> None:
        super().__init__(
            f"{reason_code}: {observed} usable samples, {required} required"
        )
        self.reason_code = reason_code
        self.observed = observed
        self.required = required


@dataclass
class TrainingResult:
    """The outcome of a training attempt — success or a reasoned refusal."""

    trained: bool
    sufficiency: DataSufficiency
    metrics: dict[str, float] = field(default_factory=dict)
    parameters: dict[str, Any] = field(default_factory=dict)
    reason_codes: list[str] = field(default_factory=list)

    @property
    def refused(self) -> bool:
        return not self.trained


class BaselineModel(ABC):
    """Base class for the Phase 4 baseline models."""

    name: str
    model_type: ModelType
    version: str = "1.0.0"

    def __init__(self) -> None:
        self._fitted = False
        self._parameters: dict[str, Any] = {}

    @property
    def fitted(self) -> bool:
        return self._fitted

    @property
    def parameters(self) -> dict[str, Any]:
        return dict(self._parameters)

    @property
    @abstractmethod
    def requirement(self) -> DataRequirement: ...

    @abstractmethod
    def _fit(self, frame: pl.DataFrame) -> tuple[dict[str, Any], dict[str, float]]:
        """Fit and return (parameters, evaluation metrics)."""

    def train(self, frame: pl.DataFrame) -> TrainingResult:
        """Train, or refuse with reasons if the data is insufficient.

        Spec §14.4: do not train a model until minimum sample and diversity
        requirements are met. Refusal is a normal outcome, not an error.
        """
        sufficiency = self.requirement.evaluate(frame)
        if not sufficiency.sufficient:
            self._fitted = False
            return TrainingResult(
                trained=False,
                sufficiency=sufficiency,
                reason_codes=sufficiency.reasons,
            )
        try:
            parameters, metrics = self._fit(frame)
        except InsufficientCapabilityData as exc:
            self._fitted = False
            return TrainingResult(
                trained=False,
                sufficiency=sufficiency,
                reason_codes=[exc.reason_code],
                metrics={"usable_samples": float(exc.observed)},
            )
        self._parameters = parameters
        self._fitted = True
        return TrainingResult(
            trained=True,
            sufficiency=sufficiency,
            metrics=metrics,
            parameters=parameters,
        )

    def _require_fitted(self) -> None:
        if not self._fitted:
            msg = f"{self.name} has not been trained; no prediction is available"
            raise RuntimeError(msg)
