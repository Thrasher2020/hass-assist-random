# Random Assist Agent

A [Home Assistant](https://www.home-assistant.io/) custom integration that adds a
**conversation agent** which answers each new conversation with a randomly-chosen
agent from a pool you configure, then stays with that agent for the whole
conversation (including follow-ups).

Use it to give "Ok Nabu" a random persona instead of always the same agent.

## Features

- Random selection among your existing conversation agents (equal odds).
- Pins the chosen agent per conversation, so multi-turn follow-ups stay consistent.
- Home Assistant Cloud / `conversation.home_assistant` is **never** chosen (hard blocklist, enforced in the UI and in code).
- Config-flow (UI) setup — no YAML required.

## Installation

### HACS

1. Add this repository as a custom repository in HACS (category **Integration**).
2. Install **Random Assist Agent**.
3. Restart Home Assistant.

### Manual

Copy the `custom_components/assist_random/` directory into your
`custom_components/` directory and restart Home Assistant.

## Configuration

1. **Settings → Devices & Services → Add Integration → Random Assist Agent**.
2. Tick the conversation agents you want in the pool.
3. In **Settings → Voice assistants**, set a voice assistant's
   **Conversation agent** to **Random Assist**.

## How it works

`Random Assist` is a `conversation` entity that forwards each message to a
randomly-chosen agent from the configured pool via `conversation.async_converse`.
The pick is keyed by `conversation_id`, so follow-ups go to the same agent.

## License

MIT — see [LICENSE](LICENSE).
