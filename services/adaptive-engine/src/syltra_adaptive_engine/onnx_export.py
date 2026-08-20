"""ONNX export and inference (spec §7.5, §22 Phase 4).

Spec §7.5 is explicit that ONNX is the portable model artifact and ONNX Runtime
the local inference engine, with joblib permitted only for development and
"never as the production model interchange format". This module is the only
place a model becomes a servable artifact.

Two guarantees matter here:

- **Round-trip equivalence.** An exported model must produce the same answers as
  the estimator it came from. Export verifies this before writing, so a broken
  artifact is never promoted.
- **Validated inference output.** Phase 4 acceptance requires it: a NaN, an
  infinity, or a wrong-shaped array is rejected at the boundary rather than
  flowing onward as a plausible-looking number.
"""

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import onnxruntime as ort
from skl2onnx import to_onnx


class OnnxExportError(RuntimeError):
    """Raised when a model cannot be exported as a trustworthy artifact."""


class InferenceOutputError(ValueError):
    """Raised when an inference result fails validation."""


@dataclass(frozen=True)
class ExportedArtifact:
    path: Path
    sha256: str
    input_name: str
    feature_count: int
    max_round_trip_error: float


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def export_estimator(
    estimator: Any,
    sample_input: np.ndarray,
    destination: Path,
    tolerance: float = 1e-4,
) -> ExportedArtifact:
    """Export a fitted scikit-learn estimator to ONNX and verify it.

    ``tolerance`` bounds the acceptable difference between the original
    estimator and the exported artifact. Exceeding it aborts the export: an
    artifact that disagrees with the model it claims to be is worse than no
    artifact, because it would pass every downstream check while being wrong.
    """
    if sample_input.ndim != 2 or sample_input.shape[0] == 0:
        msg = "sample_input must be a non-empty 2-D array shaped (rows, features)"
        raise OnnxExportError(msg)

    sample = sample_input.astype(np.float32)
    try:
        model = to_onnx(estimator, sample[:1])
    except Exception as exc:  # noqa: BLE001 - skl2onnx raises many types
        msg = f"could not convert {type(estimator).__name__} to ONNX: {exc}"
        raise OnnxExportError(msg) from exc

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(model.SerializeToString())

    session = ort.InferenceSession(
        destination.read_bytes(), providers=["CPUExecutionProvider"]
    )
    input_name = str(session.get_inputs()[0].name)
    exported = np.asarray(session.run(None, {input_name: sample})[0]).ravel()
    original = np.asarray(estimator.predict(sample_input)).ravel()

    if exported.shape != original.shape:
        destination.unlink(missing_ok=True)
        msg = (
            f"exported artifact returns shape {exported.shape}, "
            f"the estimator returns {original.shape}"
        )
        raise OnnxExportError(msg)

    error = float(np.max(np.abs(exported - original))) if original.size else 0.0
    if error > tolerance:
        destination.unlink(missing_ok=True)
        msg = (
            f"exported artifact disagrees with the estimator by {error:.6f} "
            f"(tolerance {tolerance}); refusing to keep it"
        )
        raise OnnxExportError(msg)

    return ExportedArtifact(
        path=destination,
        sha256=sha256_of(destination),
        input_name=input_name,
        feature_count=int(sample_input.shape[1]),
        max_round_trip_error=error,
    )


class OnnxPredictor:
    """Loads an artifact and serves validated predictions."""

    def __init__(self, artifact_path: Path, expected_features: int | None = None) -> None:
        if not artifact_path.is_file():
            msg = f"no ONNX artifact at {artifact_path}"
            raise OnnxExportError(msg)
        self._path = artifact_path
        self._session = ort.InferenceSession(
            artifact_path.read_bytes(), providers=["CPUExecutionProvider"]
        )
        self._input_name = str(self._session.get_inputs()[0].name)
        self._expected_features = expected_features

    @property
    def input_name(self) -> str:
        return self._input_name

    @property
    def sha256(self) -> str:
        digest: str = sha256_of(self._path)
        return digest

    def predict(self, features: np.ndarray) -> np.ndarray:
        """Run inference with input and output validation."""
        matrix = np.asarray(features, dtype=np.float32)
        if matrix.ndim == 1:
            matrix = matrix.reshape(1, -1)
        if matrix.ndim != 2:
            msg = f"inference input must be 2-D, got shape {matrix.shape}"
            raise InferenceOutputError(msg)
        if self._expected_features is not None and matrix.shape[1] != self._expected_features:
            msg = (
                f"inference input has {matrix.shape[1]} features, "
                f"the model was trained on {self._expected_features}"
            )
            raise InferenceOutputError(msg)
        if not np.all(np.isfinite(matrix)):
            msg = "inference input contains NaN or infinity"
            raise InferenceOutputError(msg)

        raw = self._session.run(None, {self._input_name: matrix})[0]
        output = np.asarray(raw, dtype=np.float64).ravel()

        # Phase 4 acceptance: inference output is validated. A model that
        # returns NaN must fail loudly rather than propagate a silent poison
        # value into a recommendation.
        if output.size != matrix.shape[0]:
            msg = f"model returned {output.size} results for {matrix.shape[0]} rows"
            raise InferenceOutputError(msg)
        if not np.all(np.isfinite(output)):
            msg = "model produced a non-finite prediction (NaN or infinity)"
            raise InferenceOutputError(msg)
        return output
