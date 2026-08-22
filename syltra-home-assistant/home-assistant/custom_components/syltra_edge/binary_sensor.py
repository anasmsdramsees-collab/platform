"""Connection-health entity (spec §27: display SYLTRA Edge connection health)."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTR_LAST_ERROR, DOMAIN
from .coordinator import SyltraEdgeCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: SyltraEdgeCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SyltraEdgeConnectionSensor(coordinator, entry)])


class SyltraEdgeConnectionSensor(CoordinatorEntity[SyltraEdgeCoordinator], BinarySensorEntity):
    """One entity: is the Edge Agent reachable and ready?"""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_has_entity_name = True
    _attr_translation_key = "edge_connection"

    def __init__(self, coordinator: SyltraEdgeCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_connection"

    @property
    def is_on(self) -> bool:
        data = self.coordinator.data or {}
        return bool(data.get("alive")) and bool(data.get("ready"))

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        # The endpoint is not exposed here: an attribute is visible in the UI
        # and in state history, and it could carry an embedded credential.
        return {ATTR_LAST_ERROR: self.coordinator.last_error}
