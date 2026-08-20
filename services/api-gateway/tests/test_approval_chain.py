"""The approval chain, over HTTP (UI-3 acceptance: SILA cannot bypass approval).

Two defects lived here, and neither had a test because every test drove the
services directly instead of through the API:

1. **Nothing created a policy decision.** `/recommendations` built proposals
   and returned them; `/approve` looked for a pending decision and found none,
   so approval was impossible through the only interface a person has.

2. **Recommendation identity changed on every read.** `build_recommendations`
   minted a fresh UUID each call, so the id a console displayed was stale by
   the next poll — and once policy evaluation moved into the read path, that
   leaked one policy decision per poll.

The safety-relevant half is that fixing (1) must not make it *easier* to act:
a shadow prediction must still be unapprovable, and approval must still produce
a fresh ALLOW rather than mutating the original request.
"""

from datetime import UTC, datetime, timedelta
from typing import Any, cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from syltra_api_gateway import Platform
from syltra_contracts import LearningMode
from syltra_security import Role, TokenStore

HOME = "home_001"


@pytest.fixture
def owner(tokens: TokenStore) -> dict[str, str]:
    token, _ = tokens.issue("occupant", Role.OWNER, {HOME}, ttl=timedelta(minutes=5))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def recommending(platform: Platform) -> Platform:
    """A home where a recommendation can actually be approved.

    Two things are needed, and the second was missing from every gateway test
    before this one, which is why the approval path was never exercised here:

    1. The §19.2 ladder must be walked to RECOMMEND, one rung at a time — it
       refuses to skip, and walking it is the only way a home gets there.

    2. The twin must know the *target's* current state. Policy denies with
       `TARGET_STATE_NOT_FRESH` when it does not, and it is right to: changing
       a setpoint you cannot read is not a safe action. The base fixture seeds
       a temperature sensor but never the air conditioner's own setpoint, so
       policy denied every proposal for a reason that had nothing to do with
       what was being tested.
    """
    from datetime import datetime

    from syltra_testing import make_envelope

    platform.twin.apply(
        make_envelope(
            capability="climate.target_temperature",
            value=23.0,
            unit="C",
            home_id=HOME,
            device_id="ac_living",
            room_id="living_room",
            occurred_at=datetime.now(tz=UTC),
        )
    )
    for mode in (LearningMode.SHADOW, LearningMode.RECOMMEND):
        platform.adaptive.set_mode(HOME, mode, actor="test")
    return platform


def recommendations(client: TestClient, owner: dict[str, str]) -> list[dict[str, Any]]:
    response = client.get(f"/v1/homes/{HOME}/recommendations", headers=owner)
    assert response.status_code == 200
    items: list[dict[str, Any]] = response.json()["items"]
    return items


# ── identity ──


def test_a_recommendation_keeps_its_identity_across_reads(
    client: TestClient, owner: dict[str, str]
) -> None:
    # A console polls. If the id changes between polls, the button a person is
    # looking at refers to something that no longer exists.
    seen = {item["recommendation_id"] for _ in range(5) for item in recommendations(client, owner)}
    first = recommendations(client, owner)
    assert first, "no recommendations; this test would prove nothing"
    assert len(seen) == len(first), seen


def test_repeated_reads_do_not_accumulate_policy_decisions(
    client: TestClient, recommending: Platform, owner: dict[str, str]
) -> None:
    # Evaluating policy on read is only safe if it is idempotent. At a
    # fifteen-second poll this would otherwise grow without bound.
    recommendations(client, owner)
    after_first = len(recommending.policy.decisions)
    for _ in range(5):
        recommendations(client, owner)
    assert len(recommending.policy.decisions) == after_first


def test_the_validity_window_does_not_slide_forward_on_every_read(
    client: TestClient, owner: dict[str, str]
) -> None:
    # "Expires 18:45" must mean it. A created_at of "now" would push the expiry
    # out on every read, so a recommendation would never expire.
    first = recommendations(client, owner)[0]
    again = recommendations(client, owner)[0]
    assert first["created_at"] == again["created_at"]
    assert first["expires_at"] == again["expires_at"]


# ── the policy decision is visible ──


def test_every_actionable_recommendation_carries_its_policy_decision(
    client: TestClient, recommending: Platform, owner: dict[str, str]
) -> None:
    # §17.9 and §21: the decision, and the reason for it, are what make the
    # proposal reviewable rather than an unexplained button.
    for item in recommendations(client, owner):
        if item["shadow"]:
            continue
        policy = item["policy"]
        assert policy is not None
        assert policy["decision"] in {
            "ALLOW",
            "DENY",
            "REQUIRE_USER_APPROVAL",
            "PREPARE_ONLY",
            "ESCALATE_TO_FIXED_SAFETY_RULE",
        }
        assert policy["reasons"], "a decision without a reason is not reviewable"
        assert policy["safety_class"]


def test_policy_judges_against_the_twin_rather_than_a_carried_value(
    client: TestClient, recommending: Platform, owner: dict[str, str]
) -> None:
    # The decision must reflect what is true now, not what was true when the
    # proposal was built.
    recommendations(client, owner)
    decision = next(iter(recommending.policy.decisions.values()))
    assert decision.input_hash, "the decision records the input it judged"


# ── approval ──


@pytest.mark.safety
def test_a_recommendation_can_be_approved_through_the_api(
    client: TestClient, recommending: Platform, owner: dict[str, str]
) -> None:
    item = next(i for i in recommendations(client, owner) if not i["shadow"])
    response = client.post(
        f"/v1/homes/{HOME}/recommendations/{item['recommendation_id']}/approve", headers=owner
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["decision"] == "ALLOW"
    # The approval is a *new* decision, so the original request stays in the
    # audit trail exactly as it was issued.
    assert body["decision_id"] != item["policy"]["decision_id"]
    assert "USER_APPROVED" in body["reason_codes"]


@pytest.mark.safety
def test_approval_still_requires_the_permission(
    client: TestClient, recommending: Platform, tokens: TokenStore, owner: dict[str, str]
) -> None:
    # Making approval possible must not make it possible for everyone.
    item = next(i for i in recommendations(client, owner) if not i["shadow"])
    guest, _ = tokens.issue("guest", Role.GUEST, {HOME}, ttl=timedelta(minutes=5))
    response = client.post(
        f"/v1/homes/{HOME}/recommendations/{item['recommendation_id']}/approve",
        headers={"Authorization": f"Bearer {guest}"},
    )
    assert response.status_code == 403


@pytest.mark.safety
def test_a_shadow_recommendation_is_never_given_an_approvable_decision(
    client: TestClient, platform: Platform, owner: dict[str, str]
) -> None:
    # Spec §19.2: a shadow prediction is recorded and compared, never acted on.
    # Creating a policy decision for one would be exactly the bypass the shadow
    # mode exists to prevent.
    platform.adaptive.set_mode(HOME, LearningMode.SHADOW, actor="test")
    items = recommendations(client, owner)
    assert items, "no shadow recommendations produced; this test would prove nothing"
    for item in items:
        assert item["shadow"] is True
        assert item["policy"] is None, "a shadow prediction must have no decision to approve"
        response = client.post(
            f"/v1/homes/{HOME}/recommendations/{item['recommendation_id']}/approve",
            headers=owner,
        )
        assert response.status_code == 404


def test_rejecting_records_a_deny_rather_than_deleting_the_request(
    client: TestClient, recommending: Platform, owner: dict[str, str]
) -> None:
    item = next(i for i in recommendations(client, owner) if not i["shadow"])
    response = client.post(
        f"/v1/homes/{HOME}/recommendations/{item['recommendation_id']}/reject", headers=owner
    )
    assert response.status_code == 200
    assert response.json()["decision"] == "DENY"


@pytest.mark.safety
def test_a_denied_recommendation_cannot_be_approved(
    client: TestClient, platform: Platform, owner: dict[str, str]
) -> None:
    # The base fixture's twin does not know the air conditioner's setpoint, so
    # policy denies with TARGET_STATE_NOT_FRESH — and is right to. Changing a
    # value you cannot read is not a safe action.
    #
    # The point of the test is what happens next: a person cannot approve past
    # that refusal, and the console has the reason to show instead of a button.
    for mode in (LearningMode.SHADOW, LearningMode.RECOMMEND):
        platform.adaptive.set_mode(HOME, mode, actor="test")

    item = next(i for i in recommendations(client, owner) if not i["shadow"])
    assert item["policy"]["decision"] == "DENY"
    assert item["policy"]["reasons"], "a refusal the user cannot read is not an explanation"

    response = client.post(
        f"/v1/homes/{HOME}/recommendations/{item['recommendation_id']}/approve", headers=owner
    )
    assert response.status_code == 404
    assert response.json()["detail"]["error"] == "NO_PENDING_APPROVAL"


def test_the_deny_reason_is_translated_for_the_household(
    client: TestClient, platform: Platform, owner: dict[str, str]
) -> None:
    # A reason code is not an explanation. §23: the person reads why, in their
    # own language, or the refusal is just a wall.
    for mode in (LearningMode.SHADOW, LearningMode.RECOMMEND):
        platform.adaptive.set_mode(HOME, mode, actor="test")

    arabic = client.get(
        f"/v1/homes/{HOME}/recommendations?locale=ar",
        headers={**owner, "Accept-Language": "ar"},
    ).json()["items"][0]
    assert arabic["policy"]["reasons"]
    for reason in arabic["policy"]["reasons"]:
        assert reason not in arabic["policy"]["reason_codes"], "untranslated reason code"


# ── confirmed-hazard response plans over HTTP ──


@pytest.mark.safety
def test_an_advisory_case_carries_no_response_plan(
    client: TestClient, platform: Platform, owner: dict[str, str]
) -> None:
    # Only a confirmation authorises a response. An advisory case that carried
    # a plan would blur exactly the line the risk state machine exists to hold.
    from syltra_testing import make_envelope

    now = datetime.now(tz=UTC)
    platform.twin.apply(
        make_envelope(
            capability="energy.power",
            value=9000.0,
            unit="W",
            home_id=HOME,
            device_id="meter",
            room_id="utility",
            occurred_at=now,
        )
    )
    home_state = platform.twin.home(HOME)
    assert home_state is not None
    platform.risk.evaluate(HOME, home_state, now, occupied=False)
    cases = client.get(f"/v1/homes/{HOME}/risks", headers=owner).json()["cases"]
    for case in cases:
        if case["advisory"]:
            assert case["response_plan"] is None, case["category"]


@pytest.mark.safety
def test_a_confirmed_hazard_reports_a_plan_that_has_dispatched_nothing(
    client: TestClient, platform: Platform, owner: dict[str, str]
) -> None:
    from syltra_testing import make_envelope

    now = datetime.now(tz=UTC)
    for capability, value, device, room in (
        ("safety.gas_alarm", True, "gas_kitchen", "kitchen"),
        ("valve.state", "open", "valve_main", "utility"),
    ):
        platform.twin.apply(
            make_envelope(
                capability=capability,
                value=value,
                unit=None,
                home_id=HOME,
                device_id=device,
                room_id=room,
                occurred_at=now,
            )
        )
    home_state = platform.twin.home(HOME)
    assert home_state is not None
    platform.risk.evaluate(HOME, home_state, now, occupied=False)

    confirmed = [
        case
        for case in client.get(f"/v1/homes/{HOME}/risks", headers=owner).json()["cases"]
        if not case["advisory"]
    ]
    assert confirmed, "no confirmed hazard; this test would prove nothing"
    plan = confirmed[0]["response_plan"]
    assert plan is not None
    assert plan["notifications"], "a confirmed hazard must at least tell someone"

    # Gas isolates rather than prepares (owner decision, 2026-08-20), so the
    # valve appears under `isolating`.
    isolating = plan["isolating"]
    assert isolating and isolating[0]["capability"] == "valve.state"
    assert isolating[0]["device_id"] == "valve_main"
    assert isolating[0]["reachable"] is True

    # And it has not been carried out, because this API never dispatches one.
    # The gateway reads state; something else acts. If that ever changes, this
    # is where it should be noticed.
    assert isolating[0]["carried_out"] is False
    assert plan["dispatched"] is False


@pytest.mark.safety
def test_no_endpoint_exists_that_would_carry_out_a_response(
    client: TestClient, owner: dict[str, str]
) -> None:
    # The plan is a description. Nothing in the API turns it into an action,
    # and this fails the moment someone adds a route that would.
    app = cast(FastAPI, client.app)
    paths = {route.path for route in app.routes if hasattr(route, "path")}
    for path in paths:
        lowered = path.lower()
        for forbidden in ("valve", "siren", "breaker", "isolate", "dispatch", "execute"):
            assert forbidden not in lowered, f"{path} could carry out a response"
