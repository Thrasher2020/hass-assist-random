"""Config flow for Random Assist Agent."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import selector

from .const import BLOCKLIST, CONF_AGENTS, DOMAIN


def _agent_options(hass: HomeAssistant) -> list[selector.SelectOptionDict]:
    """Return the selectable conversation agents, minus the blocklist."""
    options: list[selector.SelectOptionDict] = []
    for state in hass.states.async_all():
        if state.domain != "conversation" or state.entity_id in BLOCKLIST:
            continue
        label = state.attributes.get("friendly_name") or state.entity_id
        options.append(selector.SelectOptionDict(value=state.entity_id, label=label))
    return options


def _schema(hass: HomeAssistant, default: list[str] | None = None) -> vol.Schema:
    """Return the config/options schema."""
    field = selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=_agent_options(hass),
            multiple=True,
        )
    )
    if default:
        return vol.Schema({vol.Required(CONF_AGENTS, default=default): field})
    return vol.Schema({vol.Required(CONF_AGENTS): field})


class RandomAssistConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Random Assist Agent."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        if user_input is not None:
            agents = [a for a in user_input[CONF_AGENTS] if a not in BLOCKLIST]
            if not agents:
                return self.async_show_form(
                    step_id="user",
                    data_schema=_schema(self.hass, user_input[CONF_AGENTS]),
                    errors={CONF_AGENTS: "no_agents"},
                )
            return self.async_create_entry(
                title="Random Assist Agent", data={CONF_AGENTS: agents}
            )

        return self.async_show_form(step_id="user", data_schema=_schema(self.hass))

    @staticmethod
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return RandomAssistOptionsFlow(config_entry)


class RandomAssistOptionsFlow(OptionsFlow):
    """Handle options for Random Assist Agent."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        current = self._config_entry.options.get(
            CONF_AGENTS, self._config_entry.data.get(CONF_AGENTS, [])
        )

        if user_input is not None:
            agents = [a for a in user_input[CONF_AGENTS] if a not in BLOCKLIST]
            if not agents:
                return self.async_show_form(
                    step_id="init",
                    data_schema=_schema(self.hass, user_input[CONF_AGENTS]),
                    errors={CONF_AGENTS: "no_agents"},
                )
            return self.async_create_entry(data={CONF_AGENTS: agents})

        return self.async_show_form(
            step_id="init", data_schema=_schema(self.hass, current)
        )
