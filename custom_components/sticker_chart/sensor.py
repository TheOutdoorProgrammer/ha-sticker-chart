"""Sensor platform for the Sticker Chart integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .store import StickerChartStore

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Sticker Chart sensors from a config entry."""
    store: StickerChartStore = hass.data[DOMAIN]["store"]

    entities: list[SensorEntity] = []
    for child_id, child_data in store.children.items():
        entities.append(StickerBalanceSensor(store, child_id, child_data["name"]))
        entities.append(PendingRequestsSensor(store, child_id, child_data["name"]))

    async_add_entities(entities)


class StickerBalanceSensor(SensorEntity):
    """Sensor showing a child's sticker balance."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "stickers"
    _attr_icon = "mdi:star-circle"

    def __init__(
        self, store: StickerChartStore, child_id: str, child_name: str
    ) -> None:
        """Initialize the sensor."""
        self._store = store
        self._child_id = child_id
        self._child_name = child_name
        self._attr_unique_id = f"{DOMAIN}_{child_id}_balance"
        self._attr_name = f"{child_name} Sticker Balance"

    @property
    def native_value(self) -> int:
        """Return the sticker balance."""
        try:
            return self._store.get_child_balance(self._child_id)
        except ValueError:
            return 0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        try:
            history = self._store.get_child_history(self._child_id, limit=10)
            return {
                "child_id": self._child_id,
                "child_name": self._child_name,
                "recent_history": history,
            }
        except ValueError:
            return {"child_id": self._child_id, "child_name": self._child_name}

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info to group entities per child."""
        return {
            "identifiers": {(DOMAIN, self._child_id)},
            "name": f"{self._child_name}'s Sticker Chart",
            "manufacturer": "Sticker Chart",
            "model": "Child Profile",
        }

    async def async_added_to_hass(self) -> None:
        """Register update listener."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, f"{DOMAIN}_update", self._handle_update
            )
        )

    @callback
    def _handle_update(self) -> None:
        """Handle data update signal."""
        self.async_write_ha_state()


class PendingRequestsSensor(SensorEntity):
    """Sensor showing a child's pending redemption requests."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:clock-outline"

    def __init__(
        self, store: StickerChartStore, child_id: str, child_name: str
    ) -> None:
        """Initialize the sensor."""
        self._store = store
        self._child_id = child_id
        self._child_name = child_name
        self._attr_unique_id = f"{DOMAIN}_{child_id}_pending"
        self._attr_name = f"{child_name} Pending Requests"

    @property
    def native_value(self) -> int:
        """Return count of pending requests."""
        return len(self._store.get_pending_requests_for_child(self._child_id))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return pending request details."""
        requests = self._store.get_pending_requests_for_child(self._child_id)
        return {
            "child_id": self._child_id,
            "child_name": self._child_name,
            "pending_requests": requests,
        }

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info to group entities per child."""
        return {
            "identifiers": {(DOMAIN, self._child_id)},
            "name": f"{self._child_name}'s Sticker Chart",
            "manufacturer": "Sticker Chart",
            "model": "Child Profile",
        }

    async def async_added_to_hass(self) -> None:
        """Register update listener."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, f"{DOMAIN}_update", self._handle_update
            )
        )

    @callback
    def _handle_update(self) -> None:
        """Handle data update signal."""
        self.async_write_ha_state()
