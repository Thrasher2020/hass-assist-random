"""Constants for the Random Assist Agent integration."""

DOMAIN = "assist_random"

CONF_AGENTS = "agents"

# Agents that must never be chosen, even if selected in the config flow.
BLOCKLIST = {
    "conversation.home_assistant",
    "conversation.cloud_conversation_agent",
}

# Upper bound on the pinning map so a long-running instance never grows it.
MAX_PINNED = 512
