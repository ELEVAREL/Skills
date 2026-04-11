"""Nova Hub — lightweight skill and persona marketplace.

The hub is Nova's answer to OpenClaw's ClawHub. It supports two modes:

1. **Local index** — a JSON file at ~/.nova/hub/index.json listing installable skills
2. **Remote index** — same JSON format but fetched from a URL (default: env NOVA_HUB_URL)

Install operations clone/copy a skill tree into ~/.nova/skills/<id>/ where the skill
registry will discover it on next reload.
"""

from nova.hub.client import HubClient, get_hub

__all__ = ["HubClient", "get_hub"]
