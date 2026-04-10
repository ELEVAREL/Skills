# Elevarel Skills — Complete Claude Code Toolkit

> 198 skills · 45 agents · 82 commands · 14-module CLI agent · hooks · rules · contexts

A comprehensive Claude Code toolkit that transforms Claude into a full-stack engineering partner. Includes everything you need for software development workflows: from language-specific patterns to DevOps orchestration, security audits, AI-powered code analysis, and a standalone CLI assistant.

## Quick Start

### Use as a Claude Code Plugin

```bash
# Clone into Claude plugins directory
git clone https://github.com/elevarel/skills ~/.claude/plugins/elevarel-skills
```

All skills, agents, commands, hooks, and rules are auto-discovered by Claude Code.

### Use Nova Agent (Standalone CLI)

```bash
cd nova-agent
pip install -e .
export ANTHROPIC_API_KEY=your-key-here
nova
```

## Repository Structure

```
Skills/
├── .claude-plugin/       Plugin manifest
├── INDEX.md              Master index (searchable)
├── SKILLS-BY-CATEGORY.md Skills organized by topic
│
├── skills/               198 reusable skills (SKILL.md format)
├── agents/               45 specialized agent definitions
├── commands/             82 slash commands for common workflows
├── contexts/             Development context presets (dev, review, research)
├── hooks/                Event-driven automation hooks
├── rules/                Language-specific coding rules (12 languages)
│
├── nova-agent/           Standalone CLI agent (powered by Claude API)
│
├── superpowers/          Jesse Vincent's Superpowers plugin
├── everything-claude-code/ ECC community collection
├── anthropics-skills/    Official Anthropic skills
├── browser-use/          Browser automation skills
├── claude-mem/           Memory persistence system
├── humanizer/            Text humanization
├── stop-slop/            Quality control
├── ui-ux-pro-max-skill/  UI/UX design patterns
└── n8n-mcp/              n8n workflow integration
```

## Finding What You Need

| Looking for... | See |
|---------------|-----|
| All skills by name | [INDEX.md](./INDEX.md) |
| Skills by topic | [SKILLS-BY-CATEGORY.md](./SKILLS-BY-CATEGORY.md) |
| How to use a specific skill | `skills/<skill-name>/SKILL.md` |
| A specialized agent | `agents/<agent-name>.md` |
| A slash command | `commands/<command-name>.md` |
| Language coding rules | `rules/<language>/` |
| Nova Agent (CLI) | [nova-agent/README.md](./nova-agent/README.md) |

## What's Inside

### Skills (198 total)

Reusable prompt-based capabilities that Claude can invoke. Categories include:

- **DevOps & Infrastructure** (17): docker, k8s, terraform, ci-cd, observability
- **Security & Compliance** (12): auth, compliance, dependency audit, security review
- **Languages & Frameworks** (60+): python, go, rust, java, swift, kotlin, dart, php, ruby
- **Architecture Patterns** (15): microservices, event-driven, hexagonal, CQRS
- **AI & Prompts** (10): claude-api, prompt-engineering, agent-eval
- **Workflow** (15): tdd, code-review, incident-response, release-notes
- **Healthcare & Enterprise** (8): HIPAA, EMR, CDSS patterns
- **Testing** (12): e2e, load, chaos, property-based
- **And much more**

### Agents (45 total)

Specialized AI personas for domain-specific tasks:

- **Code Reviewers**: Python, Go, Rust, TypeScript, Java, C++, Kotlin, Swift, etc.
- **Build Resolvers**: Per-language build error specialists
- **Domain Experts**: Security, Performance, Database, Healthcare, DevOps
- **Workflow**: Tech Lead, Architect, Chief of Staff, Incident Commander
- **Utility**: Docs lookup, refactor cleaner, doc updater

### Commands (82 total)

Slash commands for common workflows:

- `/ship` — End-to-end feature delivery
- `/incident` — Production incident response
- `/orchestrate-task` — Mega-orchestrator for complex tasks
- `/code-review` — Multi-perspective review
- `/security-review` — Security audit
- `/perf-audit` — Performance analysis
- `/a11y` — Accessibility audit
- `/tdd` — TDD workflow
- And 74 more...

### Nova Agent

A standalone CLI tool (like Claude Code, but for your computer) that uses Claude API to:

- Organize files intelligently
- Monitor system resources with live dashboard
- Analyze codebases for security/debt/complexity
- Scaffold new projects from templates
- Manage services, packages, and dev servers
- Track productivity with streaks
- Take notes, set reminders, search files
- And everything via natural language

See [nova-agent/README.md](./nova-agent/README.md) for details.

## Installation Options

### Option 1: Everything (recommended)

```bash
git clone https://github.com/elevarel/skills ~/.claude/plugins/elevarel-skills
```

Claude Code will auto-discover all skills, agents, commands, hooks, and rules.

### Option 2: Just specific parts

Copy individual directories into your project's `.claude/` folder:

```bash
# Copy just the skills you want
cp -r skills/auth-patterns ~/.claude/skills/
cp -r agents/security-reviewer.md ~/.claude/agents/
```

### Option 3: Nova Agent only

```bash
cd nova-agent && pip install -e .
export ANTHROPIC_API_KEY=your-key-here
nova
```

## License

MIT — use, modify, and redistribute freely.

## Credits

This repo aggregates work from:
- **Elevarel** — primary curation, Nova Agent, custom skills
- **Jesse Vincent** — Superpowers plugin
- **Anthropic** — Official skills and documentation
- **ECC Community** — everything-claude-code contributions
- Various open source contributors
