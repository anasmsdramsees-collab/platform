"""SYLTRA Digital Twin Service (spec §14.2).

Maintains the current state of every home, room, device and capability, with
explicit freshness and an explicit distinction between *unknown* and *false*.
The projection is deterministic: replaying an identical event sequence
reproduces byte-identical state, which is what makes rebuild-after-loss and
audit reconstruction trustworthy.
"""

from syltra_digital_twin.core import (
    CapabilityState,
    DeviceState,
    RoomState,
    StateStatus,
    TwinProjection,
    TwinSnapshot,
)

__all__ = [
    "CapabilityState",
    "DeviceState",
    "RoomState",
    "StateStatus",
    "TwinProjection",
    "TwinSnapshot",
]
