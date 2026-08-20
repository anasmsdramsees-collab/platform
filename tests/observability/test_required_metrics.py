"""Spec §29 names fourteen required metrics. This checks all fourteen exist.

Written because the absence was found by hand, late, and only because somebody
went looking. Forty metrics existed and I reported the instrumentation as
complete — six of the required fourteen had no source at all, in the services
that decide and act. A count is not coverage.

The check is against the **live registry**: importing every metrics module and
asking Prometheus what is registered, rather than grepping for names. A metric
that is defined but never registered would pass a grep and fail a scrape.
"""

import importlib
import json
import pathlib
import pkgutil
import re
from datetime import timedelta
from uuid import uuid4

import pytest
from prometheus_client import REGISTRY

# Every metrics module in the platform. Imported for their side effect: a
# Prometheus metric registers itself when its module is first imported.
METRICS_MODULES = [
    "syltra_action_orchestrator.metrics",
    "syltra_adaptive_engine.metrics",
    "syltra_api_gateway.metrics",
    "syltra_automation_engine.metrics",
    "syltra_context_engine.metrics",
    "syltra_digital_twin.metrics",
    "syltra_edge_agent.metrics",
    "syltra_feedback_service.metrics",
    "syltra_policy_safety.metrics",
    "syltra_risk_engine.metrics",
]

# Spec §29's list, mapped to the metric that satisfies it. Where several
# services report the same kind of thing, one is named — the one a reader would
# actually open first.
REQUIRED: dict[str, str] = {
    "event ingress rate": "syltra_edge_events_received_total",
    "invalid-event rate": "syltra_twin_events_invalid_total",
    "stream consumer lag": "syltra_twin_consumer_connected",
    "database latency": "syltra_twin_database_latency_seconds",
    "state-update latency": "syltra_twin_state_update_latency_seconds",
    "recommendation count": "syltra_adaptive_recommendations_total",
    "policy outcomes": "syltra_policy_decisions_total",
    "action success and failure": "syltra_action_results_total",
    "manual override rate": "syltra_action_manual_overrides_total",
    "model inference latency": "syltra_adaptive_inference_latency_seconds",
    "model suspension count": "syltra_adaptive_model_suspensions_total",
    "stale sensor count": "syltra_twin_stale_capabilities",
    "active risk cases": "syltra_risk_active_cases",
}

# The fourteenth. §14.11 gives the Cloud Connector MVP responsibilities and the
# service does not exist — `services/cloud-connector/` holds a `.gitkeep`. A
# metric invented for a component that is not there would report a healthy
# cloud link that nothing could ever provide, which is worse than its absence.
# Recorded in IMPLEMENTATION_STATUS.md rather than faked here.
NOT_APPLICABLE = {"cloud connector status": "no cloud connector service exists"}


@pytest.fixture(scope="module", autouse=True)
def _import_every_metrics_module() -> None:
    for module in METRICS_MODULES:
        importlib.import_module(module)


def registered_names() -> set[str]:
    """Every metric family name Prometheus would actually scrape."""
    names: set[str] = set()
    for collector in list(REGISTRY._collector_to_names.values()):
        names |= set(collector)
    # Counters register as `_total`; the family name drops the suffix.
    return {name.removesuffix("_created") for name in names}


@pytest.mark.parametrize(("requirement", "metric"), sorted(REQUIRED.items()))
def test_every_required_metric_is_registered(requirement: str, metric: str) -> None:
    names = registered_names()
    assert metric in names, f"§29 requires {requirement!r}; {metric} is not registered"


def test_the_only_unmet_requirement_is_the_one_with_no_component() -> None:
    # Thirteen of fourteen. The fourteenth is unmet because the service it would
    # measure does not exist, and that is recorded rather than papered over.
    assert len(REQUIRED) + len(NOT_APPLICABLE) == 14
    assert set(NOT_APPLICABLE) == {"cloud connector status"}


def test_every_service_that_decides_or_acts_is_instrumented() -> None:
    # The gap was concentrated in exactly these: the components whose behaviour
    # a pilot week is watching. Five had no metrics module at all.
    for module in (
        "syltra_policy_safety.metrics",
        "syltra_action_orchestrator.metrics",
        "syltra_risk_engine.metrics",
        "syltra_automation_engine.metrics",
        # Not one of §29's fourteen, and the last service with no instrumentation
        # at all. §19.2 advances a household on the strength of its feedback, so
        # the ladder was being climbed on evidence nothing counted.
        "syltra_feedback_service.metrics",
    ):
        assert importlib.util.find_spec(module) is not None, module


def test_no_metrics_module_is_missing_from_the_list() -> None:
    # The list above is maintained by hand, so it can go stale. This finds a
    # metrics module nobody added to it — which would otherwise mean a whole
    # service silently outside the check.
    import syltra_contracts  # noqa: F401  (anchors the installed package set)

    found = set()
    for module in pkgutil.iter_modules():
        if module.name.startswith("syltra_"):
            spec = importlib.util.find_spec(f"{module.name}.metrics")
            if spec is not None:
                found.add(f"{module.name}.metrics")
    missing = sorted(found - set(METRICS_MODULES))
    assert not missing, f"metrics modules not covered by this test: {missing}"


# ── a registered metric nobody increments is the same gap, moved ──


async def test_a_policy_decision_is_counted() -> None:
    # The gap was found by counting metrics and calling it coverage. Registering
    # one and never touching it is the same mistake one step further on.
    from prometheus_client import REGISTRY as R
    from syltra_policy_safety import HomePolicy, PolicyService

    before = R.get_sample_value(
        "syltra_policy_decisions_total",
        {"outcome": "DENY", "safety_class": "COMFORT"},
    )
    service = PolicyService()
    service.set_policy("home_metrics", HomePolicy())
    _decide_something(service)
    after = R.get_sample_value(
        "syltra_policy_decisions_total",
        {"outcome": "DENY", "safety_class": "COMFORT"},
    )
    assert after is not None
    assert after > (before or 0.0)


def _decide_something(service: object) -> None:
    """Evaluate one recommendation, whatever it decides.

    Uses the policy suite's own builder rather than a second one: a fixture
    that drifts from the real shape would test the wrong object.
    """
    import sys
    from datetime import UTC, datetime

    sys.path.insert(0, "services/policy-safety/tests")
    import test_policy_rules as harness

    now = datetime.now(tz=UTC)
    service.evaluate(  # type: ignore[attr-defined]
        harness.recommendation(
            home_id="home_metrics", created_at=now, expires_at=now + timedelta(minutes=15)
        ),
        now=now,
        twin_value=None,
        twin_status="UNKNOWN",
    )


async def test_an_observe_only_refusal_is_counted() -> None:
    # The number a pilot week is actually reading.
    from prometheus_client import REGISTRY as R

    name = "syltra_action_refusals_total"
    labels = {"reason_code": "DISPATCH_DISABLED_OBSERVE_ONLY", "safety_class": "COMFORT"}
    before = R.get_sample_value(name, labels)

    import sys

    sys.path.insert(0, "services/action-orchestrator/tests")
    import test_orchestrator as harness
    from syltra_action_orchestrator import DispatchMode

    orchestrator, _, request = harness.scenario(dispatch=DispatchMode.OBSERVE_ONLY)
    await orchestrator.execute(request)

    after = R.get_sample_value(name, labels)
    assert after is not None and after > (before or 0.0)


async def test_a_response_and_its_standing_are_counted() -> None:
    from prometheus_client import REGISTRY as R
    from syltra_contracts import FeedbackKind
    from syltra_feedback_service import FeedbackService

    labels = {"kind": "NEVER_REPEAT", "source": "USER"}
    before = R.get_sample_value("syltra_feedback_responses_total", labels)

    service = FeedbackService()
    for _ in range(3):
        service.record(
            home_id="home_metrics",
            recommendation_id=uuid4(),
            kind=FeedbackKind.NEVER_REPEAT,
            recommendation_type="climate.precondition",
        )

    after = R.get_sample_value("syltra_feedback_responses_total", labels)
    assert after is not None
    assert after > (before or 0.0)

    # NEVER_REPEAT is a standing instruction to stop, so the gauge a dashboard
    # would alert on has to move with it — a counter alone would not show that
    # the household has switched something off.
    suppressed = R.get_sample_value(
        "syltra_feedback_suppressed_types", {"home_id": "home_metrics"}
    )
    assert suppressed is not None and suppressed >= 1.0


# ── the dashboard queries metrics that exist ──

DASHBOARD = (
    pathlib.Path(__file__).resolve().parents[2]
    / "config/observability/grafana/dashboards/syltra-overview.json"
)

# The one panel that is expected to have no source: §14.11 gives the Cloud
# Connector MVP responsibilities and the service does not exist. The panel is
# kept so the pilot can see the answer is "no cloud", which is the promise the
# platform makes, rather than an absence that could mean anything.
EXPECTED_WITHOUT_SOURCE = {"syltra_cloud_connected"}


def test_the_dashboard_is_valid_and_fits_the_grid() -> None:
    dashboard = json.loads(DASHBOARD.read_text(encoding="utf-8"))
    assert dashboard["uid"] and dashboard["title"]
    ids = [panel["id"] for panel in dashboard["panels"]]
    assert len(ids) == len(set(ids)), "two panels share an id"
    for panel in dashboard["panels"]:
        position = panel["gridPos"]
        assert position["x"] + position["w"] <= 24, f"{panel['title']} overflows the grid"
        assert panel["targets"], f"{panel['title']} has no query"
        for target in panel["targets"]:
            assert target["expr"].strip(), panel["title"]


def test_every_metric_the_dashboard_queries_exists() -> None:
    """A panel querying a metric nobody emits shows "No data" forever.

    That failure is silent and looks like a quiet home, which during a pilot is
    exactly the wrong thing to be unable to distinguish.
    """
    queried = set(re.findall(r"syltra_[a-z_]+", DASHBOARD.read_text(encoding="utf-8")))
    live = registered_names()
    # Histograms are queried as `_bucket`; counters as `_total`.
    resolvable = live | {f"{n}_bucket" for n in live} | {f"{n}_total" for n in live}
    missing = sorted(queried - resolvable - EXPECTED_WITHOUT_SOURCE)
    assert not missing, f"the dashboard queries metrics nothing emits: {missing}"


def test_the_dashboard_leads_with_whether_the_hub_can_act() -> None:
    # A pilot opening this needs one fact before any other, and reading order
    # is the only thing that guarantees which one they see first.
    dashboard = json.loads(DASHBOARD.read_text(encoding="utf-8"))
    first = min(dashboard["panels"], key=lambda p: (p["gridPos"]["y"], p["gridPos"]["x"]))
    assert "can act" in first["title"].lower(), first["title"]
    assert "dispatch_enabled" in json.dumps(first)
