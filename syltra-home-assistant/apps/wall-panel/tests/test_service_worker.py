"""The panel's offline copy of itself, exercised rather than read.

Every other test in this directory reads the front end as text. A service worker
is the one piece with real logic — what it keeps, what it refuses to keep, and
what it does when nothing answers — and reading it cannot show that the one rule
holds. `sw_harness.mjs` builds the smallest environment a service worker needs
and dispatches the browser's events at it.

Node is not part of the platform's toolchain (ADR-002: Python and uv), so this
skips where node is absent rather than adding a dependency to run the suite.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
HARNESS = HERE / "sw_harness.mjs"
NODE = shutil.which("node")


@pytest.mark.skipif(NODE is None, reason="node is not installed; the platform runs on Python")
def test_the_service_worker_keeps_the_panel_and_refuses_the_house() -> None:
    """Runs every assertion in the harness; its output names any that failed.

    The rule under test is the one that makes an offline panel safe rather than
    dangerous: the panel may keep its own face, never its own idea of the house.
    A cached light switch is worse than a blank one, because somebody trusts it.
    """
    assert NODE is not None
    result = subprocess.run(  # noqa: S603 - fixed argv, no shell
        [NODE, str(HARNESS), "../static/sw.js"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "no device state among them" in result.stdout
