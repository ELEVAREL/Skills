"""Nova Persona system — SPIRIT.md files define reusable AI personalities.

A Persona bundles a system prompt, a default skill set, a model choice, and
behavioral rules so Nova can switch between specialists on demand. This is
Nova's answer to OpenClaw's SOUL.md.

SPIRIT.md layout:
    ---
    name: string
    version: string
    description: string
    model: string                (optional — overrides ai.model)
    max_tokens: int              (optional)
    temperature: float           (optional)
    skills: [string]             (optional — skill ids to auto-load)
    tags: [string]
    greeting: string             (optional — first line when persona activates)
    ---
    # System prompt body (markdown)
"""

from nova.personas.loader import Persona, load_persona, parse_spirit_md
from nova.personas.registry import PersonaRegistry, get_persona_registry

__all__ = [
    "Persona",
    "load_persona",
    "parse_spirit_md",
    "PersonaRegistry",
    "get_persona_registry",
]
