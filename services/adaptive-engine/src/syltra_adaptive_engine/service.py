"""Adaptive Engine service in shadow mode (spec §14.4, §19.2).

The engine ingests normalized events, trains per-home models when the data
justifies it, and turns predictions into **recommendations** — advisory
proposals with no execution path (safety invariant 1).

Lifecycle enforcement lives here:

- A home starts in ``OBSERVE`` and can only advance one rung at a time, so
  ``OBSERVE → AUTHORIZED_AUTOMATION`` is impossible (spec §19.2).
- In ``SHADOW``, recommendations are generated and recorded but published to a
  **separate shadow subject**, never the recommendation subject the rest of the
  platform consumes. Nothing downstream can mistake a shadow prediction for a
  live proposal.
- Below ``RECOMMEND``, no recommendation reaches the live subject at all.
"""

import json
import logging
from collections import deque
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import NAMESPACE_URL, uuid4, uuid5

from nats.aio.msg import Msg

from syltra_adaptive_engine import metrics
from syltra_adaptive_engine.features import (
    FEATURE_SCHEMA_VERSION,
    extract_events,
    for_home,
    training_window,
)
from syltra_adaptive_engine.models import (
    EnergyAnomalyModel,
    RoutineBaselineModel,
    TemperaturePreferenceModel,
)
from syltra_adaptive_engine.drift import (
    DriftThresholds,
    DriftVerdict,
    ModelHealth,
    assess,
)
from syltra_adaptive_engine.models.base import TrainingResult
from syltra_adaptive_engine.registry import ModelRegistry, build_card
from syltra_contracts import (
    EventEnvelope,
    EventSource,
    EventSubject,
    LearningMode,
    ModelReference,
    PrivacyClass,
    Recommendation,
    RecommendationTarget,
    TrainingWindow,
    allows_recommendations,
    assert_transition,
)
from syltra_eventing import EventPublisher
from syltra_eventing.subjects import recommendation_subject, sanitize_token

logger = logging.getLogger(__name__)

RECOMMENDATION_TTL = timedelta(minutes=15)
"""Spec §15: recommendations expire. 15 minutes matches the contract example."""

HISTORY_LIMIT = 50_000
"""Bounded in-memory history so a long-running hub cannot grow without limit."""

TRAINING_CODE_REVISION = "phase4"


def shadow_subject(home_id: str) -> str:
    """Shadow predictions travel on their own subject, never the live one."""
    return f"syltra.ai.home.{sanitize_token(home_id)}.shadow"


class AdaptiveEngineService:
    def __init__(
        self,
        publisher: EventPublisher,
        hub_id: str = "hub_dev_001",
        registry: ModelRegistry | None = None,
        default_mode: LearningMode = LearningMode.OBSERVE,
    ) -> None:
        self._publisher = publisher
        self._hub_id = hub_id
        self.registry = registry or ModelRegistry()
        self._default_mode = default_mode
        self._modes: dict[str, LearningMode] = {}
        self._history: dict[str, deque[EventEnvelope]] = {}
        self._models: dict[str, dict[str, Any]] = {}
        self.shadow_log: list[Recommendation] = []
        self._health: dict[tuple[str, str], ModelHealth] = {}
        self._thresholds = DriftThresholds()
        self._ready = False

    # ── lifecycle (spec §19.2) ──

    @property
    def ready(self) -> bool:
        return self._ready

    def mark_ready(self, ready: bool = True) -> None:
        self._ready = ready
        metrics.CONSUMER_CONNECTED.set(1 if ready else 0)

    def mode(self, home_id: str) -> LearningMode:
        return self._modes.get(home_id, self._default_mode)

    def set_mode(self, home_id: str, target: LearningMode, actor: str = "operator") -> LearningMode:
        """Advance or withdraw a home's learning mode.

        Raises ``LearningModeTransitionError`` on any attempt to skip a stage —
        the ladder is enforced in the contract layer, not re-implemented here.
        """
        current = self.mode(home_id)
        assert_transition(current, target)
        self._modes[home_id] = target
        metrics.LEARNING_MODE.labels(home_id=home_id).set(_mode_rank(target))
        logger.info(
            "learning mode for %s: %s → %s (by %s)", home_id, current.value, target.value, actor
        )
        return target

    # ── ingestion ──

    async def handle_message(self, message: Msg) -> None:
        metrics.EVENTS_CONSUMED.inc()
        try:
            envelope = EventEnvelope.model_validate(json.loads(message.data))
        except (ValueError, TypeError) as exc:
            metrics.EVENTS_INVALID.inc()
            await self._publisher.publish_deadletter(
                reason_codes=["INVALID_EVENT_AT_CONSUMER"],
                error=str(exc),
                original_subject=message.subject,
            )
            await message.ack()
            return
        self.observe(envelope)
        await message.ack()

    def observe(self, envelope: EventEnvelope) -> None:
        """Record an event in the home's bounded local history."""
        if envelope.capability is None:
            return
        history = self._history.setdefault(envelope.home_id, deque(maxlen=HISTORY_LIMIT))
        history.append(envelope)
        metrics.HISTORY_SIZE.labels(home_id=envelope.home_id).set(len(history))

    def history_size(self, home_id: str) -> int:
        return len(self._history.get(home_id, ()))

    # ── training ──

    def train_home(self, home_id: str) -> dict[str, TrainingResult]:
        """Train every baseline for one home, recording versions that qualify."""
        events = list(self._history.get(home_id, ()))
        frame = for_home(extract_events(events), home_id)
        start, end = training_window(frame)

        candidates = {
            "routine_baseline": RoutineBaselineModel(),
            "temperature_preference": TemperaturePreferenceModel(),
            "energy_anomaly": EnergyAnomalyModel(),
        }
        results: dict[str, TrainingResult] = {}
        fitted: dict[str, Any] = {}

        for name, model in candidates.items():
            result = model.train(frame)
            results[name] = result
            metrics.TRAINING_ATTEMPTS.labels(model=name).inc()
            if not result.trained:
                metrics.TRAINING_REFUSALS.labels(
                    model=name, reason=result.reason_codes[0] if result.reason_codes else "UNKNOWN"
                ).inc()
                logger.info("%s: %s", name, result.sufficiency.explain())
                continue

            fitted[name] = model
            self.registry.register(
                home_id=home_id,
                name=name,
                version=model.version,
                model_type=model.model_type,
                feature_schema_version=FEATURE_SCHEMA_VERSION,
                training_code_revision=TRAINING_CODE_REVISION,
                training_window=TrainingWindow(
                    start=start,
                    end=end,
                    sample_count=result.sufficiency.sample_count,
                    distinct_days=result.sufficiency.distinct_days,
                ),
                evaluation_metrics=result.metrics,
                card=build_card(
                    model.model_type,
                    summary=f"{name} baseline trained on local household history",
                    limitations=(
                        "Trained on a single household's recent history; "
                        "predictions degrade when device coverage changes."
                    ),
                    training_data=(
                        f"{result.sufficiency.sample_count} local events across "
                        f"{result.sufficiency.distinct_days} days"
                    ),
                    evaluation=", ".join(f"{k}={v}" for k, v in result.metrics.items()),
                ),
            )
        self._models[home_id] = fitted
        return results

    def fitted_models(self, home_id: str) -> dict[str, Any]:
        return dict(self._models.get(home_id, {}))

    # ── drift and suspension (spec §19.4) ──

    def health(self, home_id: str, model_name: str) -> ModelHealth:
        """The observed health of one serving model."""
        key = (home_id, model_name)
        if key not in self._health:
            self._health[key] = ModelHealth(model_name=model_name, home_id=home_id)
        return self._health[key]

    def record_feedback(self, home_id: str, model_name: str, kind: str) -> None:
        """Feed household responses into the model's health record."""
        health = self.health(home_id, model_name)
        if kind == "ACCEPT":
            health.accepted += 1
        elif kind == "REJECT":
            health.rejected += 1
        elif kind in {"UNDO", "NEVER_REPEAT"}:
            health.undone += 1

    def record_action(self, home_id: str, model_name: str, overridden: bool = False) -> None:
        health = self.health(home_id, model_name)
        health.actions_dispatched += 1
        if overridden:
            health.manual_overrides += 1

    def record_inference_failure(self, home_id: str, model_name: str) -> None:
        self.health(home_id, model_name).consecutive_inference_failures += 1

    def record_inference_success(self, home_id: str, model_name: str) -> None:
        self.health(home_id, model_name).consecutive_inference_failures = 0

    def record_stale_sensors(self, home_id: str, model_name: str, count: int) -> None:
        self.health(home_id, model_name).stale_required_sensors = count

    def check_drift(
        self, home_id: str, now: datetime | None = None
    ) -> dict[str, DriftVerdict]:
        """Assess every serving model and suspend those that have drifted.

        Called on a timer. A model that has lost the household's trust stands
        itself down before anyone has to ask (spec §19.4).
        """
        moment = now or datetime.now(tz=UTC)
        verdicts: dict[str, DriftVerdict] = {}

        for model_name in {name for home, name in self._health if home == home_id}:
            health = self.health(home_id, model_name)
            health.last_evaluated_at = moment
            verdict = assess(health, self._thresholds)
            verdicts[model_name] = verdict
            if not verdict.suspend:
                continue
            active = self.registry.active(home_id, model_name)
            if active is None:
                # Nothing is serving; the verdict is recorded but there is
                # nothing to withdraw.
                continue
            self.registry.suspend(
                home_id,
                model_name,
                reason=verdict.explain(),
                actor="adaptive-engine:drift",
            )
            metrics.MODEL_SUSPENSIONS.labels(model=model_name).inc()
            logger.warning(
                "SUSPENDED %s for %s: %s", model_name, home_id, verdict.explain()
            )
        return verdicts

    def suspended_models(self, home_id: str) -> list[str]:
        return sorted(
            version.name
            for version in self.registry.versions(home_id)
            if version.status.value == "SUSPENDED"
        )

    # ── recommendations ──

    def build_recommendations(
        self, home_id: str, now: datetime | None = None
    ) -> list[Recommendation]:
        """Turn current predictions into advisory recommendations.

        Returns proposals; it does not publish them and cannot execute them.
        """
        moment = now or datetime.now(tz=UTC)
        models = self._models.get(home_id, {})
        shadow = self.mode(home_id) is not LearningMode.RECOMMEND and not allows_recommendations(
            self.mode(home_id)
        )
        proposals: list[Recommendation] = []

        comfort = models.get("temperature_preference")
        if comfort is not None and comfort.fitted:
            indoor = self._latest_numeric(home_id, "environment.temperature")
            prediction = comfort.predict(moment, indoor)
            device_id = self._latest_device(home_id, "climate.target_temperature")
            if device_id is not None:
                proposals.append(
                    self._recommendation(
                        home_id=home_id,
                        recommendation_type="climate.precondition",
                        device_id=device_id,
                        capability="climate.target_temperature",
                        value=prediction.value,
                        confidence=prediction.confidence,
                        reason_codes=prediction.reason_codes,
                        model_name="temperature_preference",
                        model_version=comfort.version,
                        required_policy="COMFORT_AUTOMATION",
                        created_at=moment,
                        shadow=shadow,
                        detail=prediction.detail,
                    )
                )

        routine = models.get("routine_baseline")
        if routine is not None and routine.fitted:
            prediction = routine.predict(moment)
            device_id = self._latest_device(home_id, "light.power")
            if prediction.value is True and device_id is not None:
                proposals.append(
                    self._recommendation(
                        home_id=home_id,
                        recommendation_type="lighting.routine",
                        device_id=device_id,
                        capability="light.power",
                        value=True,
                        confidence=prediction.confidence,
                        reason_codes=prediction.reason_codes,
                        model_name="routine_baseline",
                        model_version=routine.version,
                        required_policy="COMFORT_AUTOMATION",
                        created_at=moment,
                        shadow=shadow,
                        detail=prediction.detail,
                    )
                )

        for proposal in proposals:
            metrics.RECOMMENDATIONS_BUILT.labels(
                model=proposal.model.name, shadow=str(proposal.shadow).lower()
            ).inc()
        return proposals

    async def publish_recommendations(
        self, home_id: str, recommendations: list[Recommendation]
    ) -> int:
        """Publish proposals, routing by learning mode.

        Shadow proposals go to a separate subject and are recorded locally; they
        are never placed on the subject the platform treats as actionable.
        """
        mode = self.mode(home_id)
        published = 0
        for recommendation in recommendations:
            if recommendation.shadow or not allows_recommendations(mode):
                self.shadow_log.append(recommendation)
                await self._publish(shadow_subject(home_id), recommendation, shadow=True)
            else:
                await self._publish(
                    recommendation_subject(home_id), recommendation, shadow=False
                )
                published += 1
        return published

    async def _publish(
        self, subject: str, recommendation: Recommendation, shadow: bool
    ) -> None:
        envelope = EventEnvelope(
            event_id=uuid4(),
            event_type="recommendation.created",
            schema_version="1.0",
            occurred_at=recommendation.created_at,
            received_at=datetime.now(tz=UTC),
            home_id=recommendation.home_id,
            correlation_id=recommendation.recommendation_id,
            source=EventSource(
                service="adaptive-engine", instance_id=self._hub_id, protocol="internal"
            ),
            subject=EventSubject(
                device_id=recommendation.target.device_id,
                room_id=recommendation.target.room_id,
            ),
            capability=recommendation.target.capability,
            value=recommendation.proposed_value,
            quality=recommendation.confidence,
            privacy_class=PrivacyClass.HOUSEHOLD_PRIVATE,
            metadata={
                "shadow": shadow,
                "recommendation": json.loads(recommendation.model_dump_json()),
            },
        )
        await self._publisher.publish_envelope(subject, envelope)

    @staticmethod
    def _recommendation_identity(
        home_id: str,
        recommendation_type: str,
        device_id: str,
        capability: str,
        created_at: datetime,
    ) -> tuple[Any, datetime]:
        """A stable id, and the window the recommendation belongs to.

        A recommendation is a *standing proposal* for one target, not a fresh
        event each time someone looks. Minting a new id per call made a
        recommendation's identity change between two polls of the same console
        — and once policy evaluation was wired into the read path, that leaked
        one policy decision per poll, forever.

        Identity is therefore (home, type, target, window): the same proposal
        for the same target inside one validity window is the same
        recommendation, however many times it is rebuilt. The proposed value
        may be re-estimated within the window; the proposal is still the same
        one, and policy re-checks the value against the twin at approval time
        regardless.

        `created_at` becomes the window start rather than the moment of the
        call, so "suggested 18:30, expires 18:45" stays put instead of sliding
        forward on every read and never expiring.
        """
        window = int(created_at.timestamp() // RECOMMENDATION_TTL.total_seconds())
        window_start = datetime.fromtimestamp(
            window * RECOMMENDATION_TTL.total_seconds(), tz=UTC
        )
        key = f"{home_id}/{recommendation_type}/{device_id}/{capability}/{window}"
        return uuid5(NAMESPACE_URL, key), window_start

    def _recommendation(
        self,
        home_id: str,
        recommendation_type: str,
        device_id: str,
        capability: str,
        value: Any,
        confidence: float,
        reason_codes: list[str],
        model_name: str,
        model_version: str,
        required_policy: str,
        created_at: datetime,
        shadow: bool,
        detail: dict[str, Any],
    ) -> Recommendation:
        recommendation_id, window_start = self._recommendation_identity(
            home_id, recommendation_type, device_id, capability, created_at
        )
        return Recommendation(
            recommendation_id=recommendation_id,
            home_id=home_id,
            recommendation_type=recommendation_type,
            created_at=window_start,
            expires_at=window_start + RECOMMENDATION_TTL,
            target=RecommendationTarget(device_id=device_id, capability=capability),
            proposed_value=value,
            confidence=confidence,
            reason_codes=reason_codes,
            model=ModelReference(name=model_name, version=model_version),
            required_policy=required_policy,
            requires_user_approval=True,
            shadow=shadow,
            metadata={"model_detail": detail, "feature_schema": FEATURE_SCHEMA_VERSION},
        )

    # ── helpers ──

    def _latest_numeric(self, home_id: str, capability: str) -> float | None:
        for event in reversed(self._history.get(home_id, ())):
            if event.capability == capability and isinstance(event.value, int | float):
                return float(event.value)
        return None

    def _latest_device(self, home_id: str, capability: str) -> str | None:
        for event in reversed(self._history.get(home_id, ())):
            if event.capability == capability and event.subject.device_id:
                return event.subject.device_id
        return None


_MODE_RANKS = {
    LearningMode.DISABLED: 0,
    LearningMode.OBSERVE: 1,
    LearningMode.SHADOW: 2,
    LearningMode.RECOMMEND: 3,
    LearningMode.APPROVAL_REQUIRED: 4,
    LearningMode.AUTHORIZED_AUTOMATION: 5,
    LearningMode.SUSPENDED: -1,
}


def _mode_rank(mode: LearningMode) -> int:
    return _MODE_RANKS[mode]
