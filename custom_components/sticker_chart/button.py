"""Button platform for the Sticker Chart integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .store import StickerChartStore

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Sticker Chart buttons from a config entry."""
    store: StickerChartStore = hass.data[DOMAIN]["store"]

    entities: list[ButtonEntity] = []
    for child_id, child_data in store.children.items():
        for reward_id, reward_data in store.rewards.items():
            entities.append(
                RewardRedemptionButton(
                    store,
                    child_id,
                    child_data["name"],
                    reward_id,
                    reward_data,
                )
            )

    async_add_entities(entities)


class RewardRedemptionButton(ButtonEntity):
    """Button for a child to request a reward redemption."""

    _attr_has_entity_name = True

    def __init__(
        self,
        store: StickerChartStore,
        child_id: str,
        child_name: str,
        reward_id: str,
        reward_data: dict[str, Any],
    ) -> None:
        """Initialize the button."""
        self._store = store
        self._child_id = child_id
        self._child_name = child_name
        self._reward_id = reward_id
        self._reward_data = reward_data
        self._attr_unique_id = f"{DOMAIN}_{child_id}_{reward_id}_redeem"
        self._attr_name = (
            f"{child_name} - {reward_data['name']} ({reward_data['cost']} stickers)"
        )
        self._attr_icon = reward_data.get("icon", "mdi:star")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        reward = self._store.rewards.get(self._reward_id, {})
        try:
            balance = self._store.get_child_balance(self._child_id)
        except ValueError:
            balance = 0
        cost = reward.get("cost", 0)
        can_afford = balance >= cost

        # Check for pending request
        has_pending = False
        for req in self._store.pending_requests.values():
            if (
                req["child_id"] == self._child_id
                and req["reward_id"] == self._reward_id
            ):
                has_pending = True
                break

        if has_pending:
            status = "Waiting for approval"
        elif not can_afford:
            status = f"Need {cost - balance} more stickers"
        else:
            status = "Ready to redeem!"

        return {
            "child_id": self._child_id,
            "child_name": self._child_name,
            "reward_id": self._reward_id,
            "reward_name": reward.get("name", "Unknown"),
            "reward_cost": cost,
            "current_balance": balance,
            "can_afford": can_afford,
            "has_pending": has_pending,
            "status": status,
            "automation_id": reward.get("automation_id"),
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

    async def async_press(self) -> None:
        """Handle the button press — request redemption."""
        # Check for already-pending before hitting the store
        for req in self._store.pending_requests.values():
            if (
                req["child_id"] == self._child_id
                and req["reward_id"] == self._reward_id
            ):
                _LOGGER.debug("Ignoring duplicate tap for %s - already pending", self._reward_id)
                return  # Silently ignore — card will show pending state

        try:
            request_id = await self._store.async_request_redemption(
                self._child_id, self._reward_id
            )
        except ValueError as err:
            if "pending request" in str(err).lower():
                return  # Race condition — silently ignore
            raise ServiceValidationError(str(err)) from err

        reward = self._store.rewards.get(self._reward_id, {})
        self.hass.bus.async_fire(
            f"{DOMAIN}_redemption_requested",
            {
                "request_id": request_id,
                "child_id": self._child_id,
                "child_name": self._child_name,
                "reward_id": self._reward_id,
                "reward_name": reward.get("name", "Unknown"),
                "reward_cost": reward.get("cost", 0),
                "automation_id": reward.get("automation_id"),
            },
        )
        _LOGGER.info(
            "%s requested reward %s (request %s)",
            self._child_name,
            reward.get("name"),
            request_id,
        )

    async def async_added_to_hass(self) -> None:
        """Register update listener."""
        self.async_on_remove(
            self.hass.bus.async_listen(
                f"{DOMAIN}_data_updated", self._handle_update
            )
        )

    @callback
    def _handle_update(self, event: Any) -> None:
        """Handle data update signal."""
        self.async_write_ha_state()
