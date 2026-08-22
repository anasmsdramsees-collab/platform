"""The production entrypoint — the one that runs against a real house.

Between `devserver.py` (synthetic data, for looking at the console) and the four
services that expect NATS and Postgres beside them, there was no way to run this
platform on one machine against a real Home Assistant. The API gateway — which
serves the console, the panel, scenes, goals and every manual control — had no
`main` at all.

These tests hold the parts of that entrypoint that would be discovered on a
bench, expensively, if they were wrong.
"""

import ast
from pathlib import Path

import pytest
from syltra_api_gateway import hub

SOURCE = Path(hub.__file__).read_text(encoding="utf-8")


def test_a_hub_with_no_way_to_reach_the_house_refuses_to_start() -> None:
    """Rather than serving a console showing an empty house, which reads as
    "you have no devices" instead of "I am not connected"."""
    import os
    from unittest import mock

    with mock.patch.dict(os.environ, {"HOME_ASSISTANT_TOKEN": ""}, clear=False):
        with pytest.raises(SystemExit) as raised:
            import asyncio

            asyncio.run(hub.run_hub())
    assert "HOME_ASSISTANT_TOKEN" in str(raised.value)


def test_the_hub_seeds_no_synthetic_household() -> None:
    """`devserver` invents a house to look at. This one must not: a real hub
    that showed a demo light beside a real one would be worse than useless."""
    for invented in ("comfort_history", "routine_history", "make_envelope", "demo"):
        assert invented not in SOURCE, invented


def test_the_edge_agent_writes_straight_into_the_twin() -> None:
    """The seam that lets one box do without a broker: the Edge Agent takes its
    publisher as an argument, so the same service that publishes to NATS in the
    full deployment hands envelopes to the twin here. One code path, not two."""
    publisher = hub._DirectPublisher.__doc__ or ""
    assert "NATS" in publisher
    assert "publish_envelope" in SOURCE


def test_nothing_in_the_hub_imports_a_broker_or_a_database() -> None:
    """Asserted on the parsed imports rather than on a grep, because a comment
    saying "no NATS here" is not a guarantee and an import is."""
    tree = ast.parse(SOURCE)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    for forbidden in ("nats", "asyncpg", "psycopg", "sqlalchemy", "syltra_eventing"):
        assert forbidden not in imported, forbidden


def test_life_safety_stays_blocked_unless_somebody_says_otherwise() -> None:
    """The environment comes from configuration, and the example configuration
    ships as `development` — which blocks valves, breakers and sirens."""
    example = Path(hub.__file__).resolve().parents[4] / "infrastructure/systemd/hub.env.example"
    assert "SYLTRA_ENVIRONMENT=development" in example.read_text(encoding="utf-8")


def test_the_token_limit_is_stated_rather_than_discovered() -> None:
    """A bench prototype whose owner token dies on restart is fine. One that
    dies on restart without saying so costs somebody an afternoon."""
    assert "Restarting the hub invalidates it" in SOURCE


def test_a_command_is_given_time_to_be_reported_back() -> None:
    """A real device takes a moment to report the state it was just put into.
    Verifying instantly would mark every command unverified — and the
    orchestrator treats unverified as failed, which is correct and would make
    every light on the panel look broken."""
    assert "verify_delay_seconds=1.5" in SOURCE


def test_the_service_unit_restarts_and_confines_the_hub() -> None:
    root = Path(hub.__file__).resolve().parents[4]
    unit = (root / "infrastructure/systemd/syltra-hub.service").read_text(encoding="utf-8")
    # A hub that dies at three in the morning must come back by itself.
    assert "Restart=always" in unit
    # And an integration that goes wrong must not reach the rest of the disk.
    for confinement in ("NoNewPrivileges=true", "ProtectSystem=strict", "ProtectHome=true"):
        assert confinement in unit, confinement
    # Secrets come from a root-owned file, never from the unit.
    assert "EnvironmentFile=/etc/syltra/hub.env" in unit
    assert "TOKEN=" not in unit


def test_the_installer_stops_before_creating_a_credential() -> None:
    """A script that creates your token is a script that has put it
    somewhere."""
    root = Path(hub.__file__).resolve().parents[4]
    script = (root / "infrastructure/scripts/install-hub.sh").read_text(encoding="utf-8")
    assert "Long-lived access tokens" in script
    assert "HOME_ASSISTANT_TOKEN=" not in script.replace("HOME_ASSISTANT_TOKEN as", "")
