# Changelog

All notable changes to this project are documented here.

## [1.0.0] - 2026-10-02

Initial release.

- Conversation agent that forwards to a randomly-chosen agent from a configured pool.
- Per-conversation pinning so follow-ups stay with the same agent.
- Hard blocklist so `conversation.home_assistant` (Home Assistant Cloud) is never selected.
- Config-flow (UI) setup with a multi-select of available conversation agents.
- Brand icon (dice) and `mdi:dice-multiple` entity icon.
