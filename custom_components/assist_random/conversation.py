"""Conversation platform for Random Assist Agent."""

from __future__ import annotations

import logging
import random
from collections import OrderedDict
from typing import Literal

from homeassistant.components.conversation import (
    ChatLog,
    ConversationEntity,
    ConversationInput,
    ConversationResult,
    async_converse,
)
from homeassistant.components.conversation.agent_manager import async_get_agent
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import BLOCKLIST, CONF_AGENTS, MAX_PINNED

_LOGGER = logging.getLogger(__name__)


def _effective_agents(entry: ConfigEntry) -> list[str]:
    """Return the configured pool with blocklisted entries removed."""
    configured = entry.options.get(CONF_AGENTS) or entry.data.get(CONF_AGENTS, [])
    seen: set[str] = set()
    pool: list[str] = []
    for agent_id in configured:
        if agent_id in BLOCKLIST:
            _LOGGER.warning("Skipping blocklisted agent %s", agent_id)
            continue
        if agent_id in seen:
            continue
        seen.add(agent_id)
        pool.append(agent_id)
    return pool


class RandomAssistEntity(ConversationEntity):
    """Conversation agent that forwards to a randomly chosen agent."""

    _attr_has_entity_name = True
    _attr_name = "Random Assist"
    _attr_translation_key = "random_assist"
    _attr_unique_id = "random_assist"
    _attr_supports_streaming = False

    def __init__(self, hass: HomeAssistant, agents: list[str]) -> None:
        """Initialize the entity."""
        self.hass = hass
        self._agents = agents
        self._pinned: OrderedDict[str, str] = OrderedDict()

    def update_agents(self, agents: list[str]) -> None:
        """Update the pool from the options flow."""
        self._agents = agents
        self._pinned.clear()

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return the languages supported by the pool."""
        return MATCH_ALL

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        """Expose the pool for debugging."""
        return {
            "agents": self._agents,
            "valid_agents": self._valid_agents(),
        }

    def _valid_agents(self) -> list[str]:
        """Return the pool members that are currently available."""
        return [
            agent_id
            for agent_id in self._agents
            if async_get_agent(self.hass, agent_id) is not None
        ]

    def _pick(self, conversation_id: str) -> str | None:
        """Pick an agent for a conversation, pinning it for follow-ups."""
        if conversation_id in self._pinned:
            return self._pinned[conversation_id]

        valid = self._valid_agents()
        if not valid:
            return None

        chosen = random.choice(valid)
        self._pinned[conversation_id] = chosen
        while len(self._pinned) > MAX_PINNED:
            self._pinned.popitem(last=False)
        return chosen

    async def async_prepare(self, language: str | None = None) -> None:
        """Warm every agent in the pool."""
        for agent_id in self._agents:
            agent = async_get_agent(self.hass, agent_id)
            if agent is None:
                continue
            try:
                await agent.async_prepare(language)
            except Exception:  # noqa: BLE001 - best-effort warm-up
                _LOGGER.debug("Failed to prepare agent %s", agent_id, exc_info=True)

    async def _async_handle_message(
        self, user_input: ConversationInput, chat_log: ChatLog
    ) -> ConversationResult:
        """Forward the message to a randomly chosen agent."""
        language = user_input.language or self.hass.config.language

        chosen = self._pick(user_input.conversation_id)
        if chosen is None:
            _LOGGER.warning("No valid conversation agent in pool: %s", self._agents)
            response = intent.IntentResponse(language=language)
            response.async_set_error(
                intent.IntentResponseErrorCode.UNKNOWN,
                "No conversation agent is currently available",
            )
            return ConversationResult(
                response=response, conversation_id=user_input.conversation_id
            )

        try:
            return await async_converse(
                self.hass,
                text=user_input.text,
                conversation_id=user_input.conversation_id,
                context=user_input.context,
                language=user_input.language,
                agent_id=chosen,
                device_id=user_input.device_id,
                satellite_id=user_input.satellite_id,
                extra_system_prompt=user_input.extra_system_prompt,
            )
        except Exception as err:  # noqa: BLE001 - surface as a spoken error
            _LOGGER.exception("Random assist failed for agent %s", chosen)
            response = intent.IntentResponse(language=language)
            response.async_set_error(
                intent.IntentResponseErrorCode.UNKNOWN,
                f"Agent {chosen} failed: {err}",
            )
            return ConversationResult(
                response=response, conversation_id=user_input.conversation_id
            )


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the conversation platform from a config entry."""
    entity = RandomAssistEntity(hass, _effective_agents(config_entry))
    async_add_entities([entity])

    async def _update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Handle options updates."""
        entity.update_agents(_effective_agents(entry))

    config_entry.async_on_unload(config_entry.add_update_listener(_update_listener))
