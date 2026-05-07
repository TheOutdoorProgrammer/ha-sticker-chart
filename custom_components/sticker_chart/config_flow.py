"""Config flow for the Sticker Chart integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import DOMAIN


class StickerChartConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Sticker Chart."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        # Only allow one instance
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(
                title="Sticker Chart",
                data={},
            )

        return self.async_show_form(
            step_id="user",
            description_placeholders={
                "info": "This will set up the Sticker Chart integration. "
                "Use services to add children and rewards after setup."
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return StickerChartOptionsFlow()


class StickerChartOptionsFlow(OptionsFlow):
    """Handle options flow for Sticker Chart."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show the main menu."""
        return self.async_show_menu(
            step_id="init",
            menu_options=[
                "add_child",
                "remove_child",
                "add_reward",
                "remove_reward",
                "update_reward",
            ],
        )

    async def async_step_add_child(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Add a child."""
        if user_input is not None:
            store = self.hass.data[DOMAIN]["store"]
            await store.async_add_child(user_input["name"])
            # Reload integration to pick up new entities
            for entry in self.hass.config_entries.async_entries(DOMAIN):
                await self.hass.config_entries.async_reload(entry.entry_id)
            return self.async_create_entry(data={})

        return self.async_show_form(
            step_id="add_child",
            data_schema=vol.Schema(
                {vol.Required("name"): str}
            ),
        )

    async def async_step_remove_child(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Remove a child."""
        store = self.hass.data[DOMAIN]["store"]
        children = store.children

        if not children:
            return self.async_abort(reason="no_children")

        if user_input is not None:
            await store.async_remove_child(user_input["child_id"])
            for entry in self.hass.config_entries.async_entries(DOMAIN):
                await self.hass.config_entries.async_reload(entry.entry_id)
            return self.async_create_entry(data={})

        child_options = {
            child_id: f"{data['name']} ({data['stickers']} stickers)"
            for child_id, data in children.items()
        }
        return self.async_show_form(
            step_id="remove_child",
            data_schema=vol.Schema(
                {vol.Required("child_id"): vol.In(child_options)}
            ),
        )

    async def async_step_add_reward(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Add a reward."""
        if user_input is not None:
            store = self.hass.data[DOMAIN]["store"]
            await store.async_add_reward(
                name=user_input["name"],
                cost=user_input["cost"],
                icon=user_input.get("icon", "mdi:star"),
                automation_id=user_input.get("automation_id"),
            )
            for entry in self.hass.config_entries.async_entries(DOMAIN):
                await self.hass.config_entries.async_reload(entry.entry_id)
            return self.async_create_entry(data={})

        return self.async_show_form(
            step_id="add_reward",
            data_schema=vol.Schema(
                {
                    vol.Required("name"): str,
                    vol.Required("cost"): vol.All(int, vol.Range(min=1)),
                    vol.Optional("icon", default="mdi:star"): str,
                    vol.Optional("automation_id"): str,
                }
            ),
        )

    async def async_step_remove_reward(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Remove a reward."""
        store = self.hass.data[DOMAIN]["store"]
        rewards = store.rewards

        if not rewards:
            return self.async_abort(reason="no_rewards")

        if user_input is not None:
            await store.async_remove_reward(user_input["reward_id"])
            for entry in self.hass.config_entries.async_entries(DOMAIN):
                await self.hass.config_entries.async_reload(entry.entry_id)
            return self.async_create_entry(data={})

        reward_options = {
            reward_id: f"{data['name']} ({data['cost']} stickers)"
            for reward_id, data in rewards.items()
        }
        return self.async_show_form(
            step_id="remove_reward",
            data_schema=vol.Schema(
                {vol.Required("reward_id"): vol.In(reward_options)}
            ),
        )

    async def async_step_update_reward(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Update a reward."""
        store = self.hass.data[DOMAIN]["store"]
        rewards = store.rewards

        if not rewards:
            return self.async_abort(reason="no_rewards")

        if user_input is not None:
            reward_id = user_input.pop("reward_id")
            # Filter out empty optional fields
            updates = {k: v for k, v in user_input.items() if v not in (None, "")}
            if updates:
                await store.async_update_reward(reward_id, **updates)
                # Signal update to entities
                async_dispatcher_send(self.hass, f"{DOMAIN}_update")
            return self.async_create_entry(data={})

        reward_options = {
            reward_id: f"{data['name']} ({data['cost']} stickers)"
            for reward_id, data in rewards.items()
        }
        return self.async_show_form(
            step_id="update_reward",
            data_schema=vol.Schema(
                {
                    vol.Required("reward_id"): vol.In(reward_options),
                    vol.Optional("name"): str,
                    vol.Optional("cost"): vol.All(int, vol.Range(min=1)),
                    vol.Optional("icon"): str,
                    vol.Optional("automation_id"): str,
                }
            ),
        )
