# Nova Agent

Nova is an AI-powered agent platform that lives in your terminal. Point it at your
computer, your repos, or a messaging channel and let a persona-driven Claude take over.

**v0.3 makes Nova a real agent platform**, not just a CLI tool:

- **Personas (SPIRIT.md)** — swap between specialist AIs without restarting
- **Skills (SKILL.md)** — drop-in plugin architecture with dynamic tool loading
- **Memory** — SQLite-backed persistent cross-session recall with FTS search
- **Gateway** — embedded HTTP control plane so other apps can chat with Nova
- **Channels** — terminal, HTTP client, Telegram long-poll (Slack/Discord next)
- **Hub** — local or remote skill marketplace you can sync and install from

See `ARCHITECTURE.md` for the full design rationale and how Nova compares to other
agent frameworks.

## Install

```bash
cd nova-agent
pip install -e .
export ANTHROPIC_API_KEY=your-key-here
```

## Quick tour

### Interactive shell
```bash
nova                           # opens the rich terminal REPL
```

Inside the shell, type naturally ("organize my Downloads") or use slash commands:

| Category | Commands |
| --- | --- |
| **Persona** | `/persona list`, `/persona use dev-sentinel`, `/persona show researcher` |
| **Skills** | `/skills list`, `/skills reload`, `/skills enable git-helper`, `/skills search git` |
| **Memory** | `/mem list`, `/mem add project "API freeze"::"Locks next Thursday"`, `/mem recall auth` |
| **Hub** | `/hub refresh`, `/hub list`, `/hub install web-fetch-extra` |
| **Gateway** | `/gateway start`, `/gateway status`, `/gateway stop` |

Type `/help` for the full menu (files, code, services, network, git, search, clipboard, etc.).

### Non-interactive commands

```bash
# Single-shot chat
nova ask "what's using the most disk space?"
nova ask-as researcher "latest benchmarks for Claude Sonnet vs GPT-5"

# Personas
nova persona list
nova persona show dev-sentinel

# Skills
nova skills list
nova skills reload

# Memory
nova memory add feedback "terse output" "user wants no trailing summaries"
nova memory recall deploy

# Hub
nova hub refresh
nova hub list
nova hub install web-fetch-extra

# Gateway (HTTP API on port 7878)
nova gateway start           # foreground, Ctrl+C to stop
nova gateway status

# Channels
TELEGRAM_BOT_TOKEN=... nova channel telegram --persona nova-default
```

## Concepts

### Personas (SPIRIT.md)

A persona is a named AI personality: system prompt, default skill set, model choice,
and behavioural rules. Nova ships with four:

- `nova-default` — friendly terse concierge
- `dev-sentinel` — senior pair-programmer for git and code
- `researcher` — deep-research mode with mandatory citations
- `automator` — background ops and scheduling

Add your own under `~/.nova/personas/<id>/SPIRIT.md`. Frontmatter fields:
```yaml
---
name: my-persona
version: 0.1.0
description: One-liner
model: claude-sonnet-4-20250514   # optional override
skills: [git-helper, web-fetch]   # auto-load these skills
tags: [dev]
greeting: "Hey, ready to work."
---
# System prompt markdown body...
```

### Skills (SKILL.md)

A skill is a directory with a `SKILL.md` manifest and an optional `tools.py`. Nova
discovers skills in two places: `nova-agent/skills/` (builtins) and `~/.nova/skills/`
(user skills + hub installs). Drop a skill in and it shows up after `/skills reload`.

A `tools.py` exposes two things:

```python
TOOLS = [
    {
        "name": "my_tool",
        "description": "What it does",
        "input_schema": {"type": "object", "properties": {...}, "required": [...]},
    },
]

def execute(name: str, input_data: dict) -> str:
    ...
```

Built-in skills: `git-helper`, `web-fetch`, `screenshot`.

### Memory

Persistent memories live in `~/.nova/memory.db`. Nova's brain automatically injects
the most recent memories into every system prompt so past context carries over.
Typed entries (`user`, `feedback`, `project`, `reference`, `fact`) are searchable
via SQLite FTS5 when available.

### Gateway

`nova gateway start` spins up a local HTTP API (`127.0.0.1:7878`) with bearer-token
auth (token stored in `~/.nova/gateway.token`). Endpoints:

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/healthz` | Liveness |
| GET | `/v1/personas` | List personas |
| POST | `/v1/personas/active` | Switch active persona |
| GET | `/v1/skills` | List skills |
| POST | `/v1/skills/toggle` | Enable/disable a skill |
| POST | `/v1/chat` | Run a chat turn |
| GET | `/v1/memory` | List memories |
| POST | `/v1/memory` | Add a memory |

### Channels

A channel is a transport that pipes user messages into the brain. Shipped:

- **terminal** — the default REPL (`nova`)
- **http_client** — Python client against the gateway (used by other adapters)
- **telegram** — long-poll Telegram bot (`nova channel telegram`)

Slack, Discord, and WebSocket channels are the next targets.

## Requirements

- Python 3.10+
- `ANTHROPIC_API_KEY` for AI features (file organizer and system tools work without it)
