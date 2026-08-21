"""SYLTRA Action Orchestrator (spec §14.7).

The only component that commands a device. Every action is idempotent,
traceable, time-bounded, verified against the device's reported state, and
reversible where the capability supports it (spec §0 rule 15).
"""

from syltra_action_orchestrator.orchestrator import (
    DispatchMode,
    ActionOrchestrator,
    ActionRefused,
    AuditEntry,
    OrchestratorConfig,
    build_action_request,
    build_manual_action,
)

__all__ = [
    "DispatchMode",
    "ActionOrchestrator",
    "ActionRefused",
    "AuditEntry",
    "OrchestratorConfig",
    "build_action_request",
    "build_manual_action",
]
