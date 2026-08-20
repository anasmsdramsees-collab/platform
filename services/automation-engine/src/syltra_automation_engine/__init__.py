"""SYLTRA Automation Engine — deterministic, user-authored rules (spec §2.3).

Imports nothing from the Adaptive Engine: safety invariant 7 requires fixed
automations to keep working when every model is suspended.
"""

from syltra_automation_engine.engine import (
    ECHO_WINDOW,
    AutomationEngine,
    AutomationProposal,
    Evaluation,
    SkipReason,
)

__all__ = [
    "ECHO_WINDOW",
    "AutomationEngine",
    "AutomationProposal",
    "Evaluation",
    "SkipReason",
]
