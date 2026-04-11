# Nova Agent — Architecture

Nova is an **agent platform**, not just a CLI. The goal is to be a serious open
alternative to OpenClaw: run your own personal AI assistant, on your own machine,
reachable from wherever you chat.

## Layered design

```
                ┌──────────────────────────────────────────────┐
Channels        │ terminal   http_client   telegram   …        │
                └──────────────┬───────────────────────────────┘
                               ▼
                ┌──────────────────────────────────────────────┐
Gateway         │  HTTP control plane  (/v1/chat, /v1/personas,│
                │   /v1/skills, /v1/memory)  — bearer auth     │
                └──────────────┬───────────────────────────────┘
                               ▼
                ┌──────────────────────────────────────────────┐
Brain           │  AIBrain  (persona + memory + tools)         │
                │  - builds system prompt per turn             │
                │  - merges core tools + skill tools           │
                │  - routes tool_use to the right executor     │
                └────┬────────────┬────────────────┬───────────┘
                     ▼            ▼                ▼
                Personas      Skills           Memory
                (SPIRIT.md)   (SKILL.md)       (SQLite + FTS)
                     │            │                │
                     ▼            ▼                ▼
                PersonaRegistry SkillRegistry   MemoryStore
                     │            │
                     └──────┐ ┌───┘
                            ▼ ▼
                            Hub (local/remote index)
```

Each layer is replaceable without touching its neighbours:

- Add a channel → adapter calls the brain or gateway, nothing else changes
- Add a skill → drop a directory into `~/.nova/skills/<id>/`, call `/skills reload`
- Add a persona → drop a `SPIRIT.md` into `~/.nova/personas/<id>/`
- Run in a new environment → pick the right subset of skills, keep the same brain

## Why this beats a monolithic CLI

The previous Nova (v0.2) was a set of slash commands wired directly into a
`TOOLS = [...]` list. Adding a capability meant editing `ai_brain.py`,
`cli.py`, and writing a module. v0.3 cuts that down to: drop a folder, reload.

Skills are first-class:
- Each skill is isolated in its own import namespace (safe to crash)
- Tool definitions are read from `TOOLS` at runtime, not hardcoded
- The registry finds the skill that owns a tool name and dispatches automatically

Personas are first-class:
- System prompt, model, skill whitelist, and greeting all configurable
- Switching personas is instant (`/persona use ...`) — no new process
- Each persona can pin its own model; `dev-sentinel` could use Opus while
  `researcher` stays on Sonnet

Memory is first-class:
- SQLite lives forever at `~/.nova/memory.db`
- Recent memories are injected into every system prompt automatically
- `memory_remember`/`memory_recall`/`memory_forget` are exposed as tools so
  the model can ask to persist things

## Comparison with OpenClaw

| Concept | OpenClaw | Nova |
| --- | --- | --- |
| Agent definition | `SOUL.md` | `SPIRIT.md` |
| Plugin unit | bundled plugins + ClawHub | `SKILL.md` + Nova Hub |
| Control plane | Gateway (TS/Node) | Gateway (Python stdlib HTTP) |
| Channels | 20+ (Telegram, Slack, WhatsApp, iMessage, …) | terminal + http_client + telegram (starter set) |
| Runtime | Node.js | Python 3.10+ |
| Memory | plugin-provided | built-in SQLite + FTS5 |
| Install weight | heavy (Node + plugin deps) | light (4 stdlib modules + anthropic + rich + click) |
| Self-hosted | ✔ | ✔ |

Nova isn't trying to match OpenClaw channel-for-channel. The bet is that a
smaller, Python-native core with clean extension surfaces (skills + personas)
is easier to fork, read, and extend than a 20-channel Node monolith — especially
for users who already live in Claude Code / Python tooling.

## Directory layout

```
nova-agent/
├── nova/
│   ├── cli.py                  # Click commands + interactive shell
│   ├── config.py               # yaml config + user dirs
│   ├── channels/               # transport adapters
│   │   ├── base.py
│   │   ├── http_client.py
│   │   └── telegram.py
│   ├── gateway/                # HTTP control plane (stdlib only)
│   │   └── server.py
│   ├── hub/                    # skill marketplace client
│   │   └── client.py
│   ├── personas/               # SPIRIT.md loader + registry
│   │   ├── loader.py
│   │   └── registry.py
│   ├── skills/                 # SKILL.md loader + registry
│   │   ├── loader.py
│   │   └── registry.py
│   ├── modules/                # core capabilities (organizer, ai_brain, memory, …)
│   │   ├── ai_brain.py         # persona-aware brain, dynamic tool merge
│   │   ├── memory.py           # SQLite + FTS5 persistence
│   │   └── … (organizer, system, network, git, etc.)
│   └── utils/display.py        # rich terminal theme
├── personas/                   # shipped personas
│   ├── nova-default/SPIRIT.md
│   ├── dev-sentinel/SPIRIT.md
│   ├── researcher/SPIRIT.md
│   └── automator/SPIRIT.md
└── skills/                     # shipped skills
    ├── git-helper/
    ├── web-fetch/
    └── screenshot/
```

User directories under `~/.nova/`:

```
~/.nova/
├── config.yaml                 # base config
├── organize_rules.yaml         # file organizer rules
├── memory.db                   # persistent memory
├── gateway.token               # bearer token for gateway auth
├── personas/                   # user-installed personas
├── skills/                     # user-installed + hub skills
├── hub/index.json              # hub index cache
└── screenshots/                # screenshot skill output
```

## Adding a new skill

1. `mkdir ~/.nova/skills/my-skill`
2. Create `SKILL.md`:
   ```markdown
   ---
   name: my-skill
   version: 0.1.0
   description: what it does
   tools: [my_tool]
   ---
   Full docs here.
   ```
3. Create `tools.py` with `TOOLS = [...]` and `def execute(name, input_data): ...`
4. `nova skills reload` — it's now in every persona's tool list.

## Adding a new persona

1. `mkdir ~/.nova/personas/my-persona`
2. Create `SPIRIT.md` with frontmatter + system prompt body.
3. `nova persona list` to confirm, then `nova ask-as my-persona "..."`.

## Next up

- Slack and Discord channels
- Plugin sandboxing (import isolation + time/cpu caps)
- Streaming HTTP (SSE) from the gateway
- Remote hub index with signing + version pinning
