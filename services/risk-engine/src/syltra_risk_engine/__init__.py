"""SYLTRA Risk Engine and Safety Governor (spec §14.5, §22 Phase 6).

Two components with deliberately different authority:

- `RiskEngineService` aggregates evidence and raises **advisory** WATCH and
  PRE_ALERT cases. It never dispatches a device action (§14.5).
- `SafetyGovernor` is the only component that may confirm a hazard, and does so
  from certified alarm capabilities through deterministic rules that require no
  model, context engine or network service (safety invariants 6, 7, 17, 18).
"""

from syltra_risk_engine.governor import (
    CONFIRMATION_RULES,
    GOVERNOR_VERSION,
    Confirmation,
    ConfirmationRule,
    SafetyGovernor,
)
from syltra_risk_engine.rules import (
    RISK_RULES_VERSION,
    RiskInput,
    RiskProposal,
    evaluate_all,
)
from syltra_risk_engine.service import CaseChange, RiskEngineService

__all__ = [
    "CONFIRMATION_RULES",
    "GOVERNOR_VERSION",
    "RISK_RULES_VERSION",
    "CaseChange",
    "Confirmation",
    "ConfirmationRule",
    "RiskEngineService",
    "RiskInput",
    "RiskProposal",
    "SafetyGovernor",
    "evaluate_all",
]
