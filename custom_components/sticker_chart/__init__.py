"""The Sticker Chart integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import (
    ATTR_AMOUNT,
    ATTR_AUTOMATION_ID,
    ATTR_CHILD_ID,
    ATTR_CHILD_NAME,
    ATTR_REASON,
    ATTR_REQUEST_ID,
    ATTR_REWARD_COST,
    ATTR_REWARD_ICON,
    ATTR_REWARD_ID,
    ATTR_REWARD_NAME,
    DOMAIN,
    EVENT_REDEMPTION_APPROVED,
    EVENT_REDEMPTION_DENIED,
    EVENT_REDEMPTION_REQUESTED,
    EVENT_STICKERS_GRANTED,
    EVENT_STICKERS_REVOKED,
    PLATFORMS,
    SERVICE_ADD_CHILD,
    SERVICE_ADD_REWARD,
    SERVICE_APPROVE_REDEMPTION,
    SERVICE_DENY_REDEMPTION,
    SERVICE_GRANT_STICKERS,
    SERVICE_REMOVE_CHILD,
    SERVICE_REMOVE_REWARD,
    SERVICE_REQUEST_REDEMPTION,
    SERVICE_REVOKE_STICKERS,
    SERVICE_UPDATE_REWARD,
)
from .store import StickerChartStore

_LOGGER = logging.getLogger(__name__)

type StickerChartConfigEntry = ConfigEntry


async def async_setup_entry(hass: HomeAssistant, entry: StickerChartConfigEntry) -> bool:
    """Set up Sticker Chart from a config entry."""
    store = StickerChartStore(hass)
    await store.async_load()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["store"] = store

    _register_services(hass, store)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: StickerChartConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.pop(DOMAIN, None)
    return unload_ok


def _get_store(hass: HomeAssistant) -> StickerChartStore:
    """Get the store, raising if not loaded."""
    store = hass.data.get(DOMAIN, {}).get("store")
    if store is None:
        raise ServiceValidationError("Sticker Chart integration not loaded")
    return store


def _register_services(hass: HomeAssistant, store: StickerChartStore) -> None:
    """Register all sticker chart services."""

    # Skip if services already registered (multiple config entries)
    if hass.services.has_service(DOMAIN, SERVICE_ADD_CHILD):
        return

    async def handle_add_child(call: ServiceCall) -> None:
        """Handle adding a child."""
        s = _get_store(hass)
        name = call.data[ATTR_CHILD_NAME]
        try:
            child_id = await s.async_add_child(name)
        except ValueError as err:
            raise ServiceValidationError(str(err)) from err
        # Reload platforms to create new entities
        for entry in hass.config_entries.async_entries(DOMAIN):
            await hass.config_entries.async_reload(entry.entry_id)
        _LOGGER.info("Added child %s with ID %s", name, child_id)

    async def handle_remove_child(call: ServiceCall) -> None:
        """Handle removing a child."""
        s = _get_store(hass)
        child_id = call.data[ATTR_CHILD_ID]
        try:
            await s.async_remove_child(child_id)
        except ValueError as err:
            raise ServiceValidationError(str(err)) from err
        for entry in hass.config_entries.async_entries(DOMAIN):
            await hass.config_entries.async_reload(entry.entry_id)

    async def handle_grant_stickers(call: ServiceCall) -> None:
        """Handle granting stickers."""
        s = _get_store(hass)
        child_id = call.data[ATTR_CHILD_ID]
        amount = call.data[ATTR_AMOUNT]
        reason = call.data.get(ATTR_REASON, "")
        try:
            new_balance = await s.async_grant_stickers(child_id, amount, reason)
        except ValueError as err:
            raise ServiceValidationError(str(err)) from err
        hass.bus.async_fire(
            EVENT_STICKERS_GRANTED,
            {
                "child_id": child_id,
                "child_name": s.get_child_name(child_id),
                "amount": amount,
                "reason": reason,
                "new_balance": new_balance,
            },
        )
        # Signal entities to update
        _signal_update(hass)

    async def handle_revoke_stickers(call: ServiceCall) -> None:
        """Handle revoking stickers."""
        s = _get_store(hass)
        child_id = call.data[ATTR_CHILD_ID]
        amount = call.data[ATTR_AMOUNT]
        reason = call.data.get(ATTR_REASON, "")
        try:
            new_balance = await s.async_revoke_stickers(child_id, amount, reason)
        except ValueError as err:
            raise ServiceValidationError(str(err)) from err
        hass.bus.async_fire(
            EVENT_STICKERS_REVOKED,
            {
                "child_id": child_id,
                "child_name": s.get_child_name(child_id),
                "amount": amount,
                "reason": reason,
                "new_balance": new_balance,
            },
        )
        _signal_update(hass)

    async def handle_add_reward(call: ServiceCall) -> None:
        """Handle adding a reward."""
        s = _get_store(hass)
        name = call.data[ATTR_REWARD_NAME]
        cost = call.data[ATTR_REWARD_COST]
        icon = call.data.get(ATTR_REWARD_ICON, "mdi:star")
        automation_id = call.data.get(ATTR_AUTOMATION_ID)
        try:
            await s.async_add_reward(name, cost, icon, automation_id)
        except ValueError as err:
            raise ServiceValidationError(str(err)) from err
        # Reload to create new button entities
        for entry in hass.config_entries.async_entries(DOMAIN):
            await hass.config_entries.async_reload(entry.entry_id)

    async def handle_remove_reward(call: ServiceCall) -> None:
        """Handle removing a reward."""
        s = _get_store(hass)
        reward_id = call.data[ATTR_REWARD_ID]
        try:
            await s.async_remove_reward(reward_id)
        except ValueError as err:
            raise ServiceValidationError(str(err)) from err
        for entry in hass.config_entries.async_entries(DOMAIN):
            await hass.config_entries.async_reload(entry.entry_id)

    async def handle_update_reward(call: ServiceCall) -> None:
        """Handle updating a reward."""
        s = _get_store(hass)
        reward_id = call.data[ATTR_REWARD_ID]
        updates: dict[str, Any] = {}
        if ATTR_REWARD_NAME in call.data:
            updates["name"] = call.data[ATTR_REWARD_NAME]
        if ATTR_REWARD_COST in call.data:
            updates["cost"] = call.data[ATTR_REWARD_COST]
        if ATTR_REWARD_ICON in call.data:
            updates["icon"] = call.data[ATTR_REWARD_ICON]
        if ATTR_AUTOMATION_ID in call.data:
            updates["automation_id"] = call.data[ATTR_AUTOMATION_ID]
        if not updates:
            raise ServiceValidationError("No fields to update")
        try:
            await s.async_update_reward(reward_id, **updates)
        except ValueError as err:
            raise ServiceValidationError(str(err)) from err
        _signal_update(hass)

    async def handle_request_redemption(call: ServiceCall) -> None:
        """Handle a child requesting to redeem a reward."""
        s = _get_store(hass)
        child_id = call.data[ATTR_CHILD_ID]
        reward_id = call.data[ATTR_REWARD_ID]
        try:
            request_id = await s.async_request_redemption(child_id, reward_id)
        except ValueError as err:
            raise ServiceValidationError(str(err)) from err
        reward = s.rewards[reward_id]
        child_name = s.get_child_name(child_id)
        hass.bus.async_fire(
            EVENT_REDEMPTION_REQUESTED,
            {
                "request_id": request_id,
                "child_id": child_id,
                "child_name": child_name,
                "reward_id": reward_id,
                "reward_name": reward["name"],
                "reward_cost": reward["cost"],
                "automation_id": reward.get("automation_id"),
            },
        )
        _signal_update(hass)

    async def handle_approve_redemption(call: ServiceCall) -> None:
        """Handle approving a redemption request."""
        s = _get_store(hass)
        request_id = call.data[ATTR_REQUEST_ID]
        try:
            result = await s.async_approve_redemption(request_id)
        except ValueError as err:
            raise ServiceValidationError(str(err)) from err
        hass.bus.async_fire(EVENT_REDEMPTION_APPROVED, result)
        _signal_update(hass)

    async def handle_deny_redemption(call: ServiceCall) -> None:
        """Handle denying a redemption request."""
        s = _get_store(hass)
        request_id = call.data[ATTR_REQUEST_ID]
        try:
            result = await s.async_deny_redemption(request_id)
        except ValueError as err:
            raise ServiceValidationError(str(err)) from err
        hass.bus.async_fire(EVENT_REDEMPTION_DENIED, result)
        _signal_update(hass)

    # Register all services
    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_CHILD,
        handle_add_child,
        schema=vol.Schema({vol.Required(ATTR_CHILD_NAME): cv.string}),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REMOVE_CHILD,
        handle_remove_child,
        schema=vol.Schema({vol.Required(ATTR_CHILD_ID): cv.string}),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_GRANT_STICKERS,
        handle_grant_stickers,
        schema=vol.Schema(
            {
                vol.Required(ATTR_CHILD_ID): cv.string,
                vol.Required(ATTR_AMOUNT): cv.positive_int,
                vol.Optional(ATTR_REASON, default=""): cv.string,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REVOKE_STICKERS,
        handle_revoke_stickers,
        schema=vol.Schema(
            {
                vol.Required(ATTR_CHILD_ID): cv.string,
                vol.Required(ATTR_AMOUNT): cv.positive_int,
                vol.Optional(ATTR_REASON, default=""): cv.string,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_REWARD,
        handle_add_reward,
        schema=vol.Schema(
            {
                vol.Required(ATTR_REWARD_NAME): cv.string,
                vol.Required(ATTR_REWARD_COST): cv.positive_int,
                vol.Optional(ATTR_REWARD_ICON, default="mdi:star"): cv.string,
                vol.Optional(ATTR_AUTOMATION_ID): cv.string,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REMOVE_REWARD,
        handle_remove_reward,
        schema=vol.Schema({vol.Required(ATTR_REWARD_ID): cv.string}),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE_REWARD,
        handle_update_reward,
        schema=vol.Schema(
            {
                vol.Required(ATTR_REWARD_ID): cv.string,
                vol.Optional(ATTR_REWARD_NAME): cv.string,
                vol.Optional(ATTR_REWARD_COST): cv.positive_int,
                vol.Optional(ATTR_REWARD_ICON): cv.string,
                vol.Optional(ATTR_AUTOMATION_ID): cv.string,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REQUEST_REDEMPTION,
        handle_request_redemption,
        schema=vol.Schema(
            {
                vol.Required(ATTR_CHILD_ID): cv.string,
                vol.Required(ATTR_REWARD_ID): cv.string,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_APPROVE_REDEMPTION,
        handle_approve_redemption,
        schema=vol.Schema({vol.Required(ATTR_REQUEST_ID): cv.string}),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_DENY_REDEMPTION,
        handle_deny_redemption,
        schema=vol.Schema({vol.Required(ATTR_REQUEST_ID): cv.string}),
    )


SIGNAL_STICKER_UPDATE = f"{DOMAIN}_update"


@callback
def _signal_update(hass: HomeAssistant) -> None:
    """Signal all sticker chart entities to update their state."""
    async_dispatcher_send(hass, SIGNAL_STICKER_UPDATE)
