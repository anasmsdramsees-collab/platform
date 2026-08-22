"""SYLTRA Policy and Safety Service (spec §14.6).

The gate every action passes through (safety invariant 2). Its rules are
deterministic and pure, so they are testable without ML services running
(invariant 17) and keep working when the Adaptive Engine is offline
(invariant 7).
"""

from syltra_policy_safety.rules import (
    POLICY_RULES_VERSION,
    RULE_CHAIN,
    HomePolicy,
    PolicyInput,
    RuleVerdict,
    evaluate_chain,
)
from syltra_policy_safety.service import PolicyService

__all__ = [
    "POLICY_RULES_VERSION",
    "RULE_CHAIN",
    "HomePolicy",
    "PolicyInput",
    "PolicyService",
    "RuleVerdict",
    "evaluate_chain",
]
