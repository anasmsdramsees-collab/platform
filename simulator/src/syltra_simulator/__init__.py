"""SYLTRA deterministic simulator (spec §23).

Provides a virtual home fixture and a mock Home Assistant WebSocket boundary
(spec §24.3 explicitly allows a mock boundary) so the whole platform runs and
tests without physical devices — and without real household data (spec §26:
synthetic data only in development and tests).
"""

from syltra_simulator.home import VIRTUAL_HOME_STATES, VirtualDevice, virtual_devices
from syltra_simulator.mock_ha import MockHomeAssistant
from syltra_simulator.scenarios import SCENARIOS, Scenario, ScenarioStep

__all__ = [
    "SCENARIOS",
    "VIRTUAL_HOME_STATES",
    "MockHomeAssistant",
    "Scenario",
    "ScenarioStep",
    "VirtualDevice",
    "virtual_devices",
]
