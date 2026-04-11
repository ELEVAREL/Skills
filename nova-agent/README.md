# Nova Agent

> A personal AI that lives on your computer. Pay once. Text it from your phone.

Nova is a self-hosted AI agent platform with personas, skills, persistent
memory, a local gateway, and channel adapters. Your hardware, your API key,
your own Telegram bot, nothing in the middle.

## Try it

**Landing page and pricing:** https://elevarel.github.io/Skills/

Nova is a commercial product from [Elevare Studio](https://elevare.studio).
The source in this repo is only the marketing site (`nova-site/`). The Nova
runtime itself is distributed as a signed pip package to license holders.

## What's here

This folder in the public repo contains:

- `nova-site/` — the marketing landing page (published automatically to
  GitHub Pages via `.github/workflows/pages.yml`)
- `README.md` — you are here

That's it. The Python source, personas, skills, gateway, onboard wizard,
service installer, and tunnel modules live in a private commercial repo and
ship to buyers via a license-gated install.

## Buy Nova

| Tier | Price | What you get |
| --- | --- | --- |
| **Spark** | $49 once | Terminal REPL, personas, skills, memory |
| **Home** | $149 once | Spark + gateway + Telegram + Cloudflare Tunnel + auto-start service |
| **Pro** | $299 once | Home + Slack, Discord, WhatsApp-Web + premium personas |
| **Lifetime** | $499 once | Pro + forever updates + 1h custom tuning |

All tiers include the onboard wizard that gets you from install to textable
in five minutes, no manual config.

## Questions

- **Is the code open source?** No. Nova is a commercial product distributed
  under a per-seat license. The source is in a private repo.
- **Do I need a server?** No. Nova runs on your own computer.
- **Do I need to pay for hosting?** No. Cloudflare Tunnel gives you a free
  public URL and your own Telegram bot is the channel.
- **Do you see my data?** No. Nothing touches Elevare servers except the
  one-time license activation ping. Your messages go Telegram → tunnel →
  your machine → Anthropic → back.

Contact: [hello@elevare.studio](mailto:hello@elevare.studio)
