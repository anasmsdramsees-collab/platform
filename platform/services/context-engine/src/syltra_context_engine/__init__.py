"""SYLTRA Context Engine (spec §14.3).

Infers what is happening in the household — occupancy, activity, environmental
concern — from the Digital Twin's current state, using **deterministic rules
before any machine learning**. Every context carries the evidence that produced
it, a confidence that degrades when signals are missing or stale, and an expiry
it cannot outlive.

Two contexts are advisory only: ``POSSIBLE_GAS_RISK`` and
``POSSIBLE_WATER_LEAK`` may raise awareness but can never confirm an emergency
(safety invariants 6 and 18).
"""

from syltra_context_engine.engine import ChangeKind, ContextChange, ContextEngine
from syltra_context_engine.rules import (
    ALL_RULES,
    RULES_VERSION,
    ContextProposal,
    RuleContext,
    evaluate_all,
)

__all__ = [
    "ALL_RULES",
    "RULES_VERSION",
    "ChangeKind",
    "ContextChange",
    "ContextEngine",
    "ContextProposal",
    "RuleContext",
    "evaluate_all",
]
