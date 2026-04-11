"""Persona registry — discovers and activates SPIRIT.md personas."""

from __future__ import annotations

from pathlib import Path

from nova.personas.loader import Persona, load_persona

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
BUILTIN_PERSONAS_DIR = _PACKAGE_ROOT / "personas"
USER_PERSONAS_DIR = Path.home() / ".nova" / "personas"


class PersonaRegistry:
    def __init__(self):
        self.personas: dict[str, Persona] = {}
        self.active_id: str | None = None
        self._loaded = False

    def discover(self) -> None:
        self.personas.clear()
        for base in (BUILTIN_PERSONAS_DIR, USER_PERSONAS_DIR):
            if not base.exists():
                continue
            # Support both directories-with-SPIRIT.md and flat *.md files
            for entry in sorted(base.iterdir()):
                if entry.is_dir():
                    p = load_persona(entry)
                elif entry.suffix.lower() == ".md":
                    p = load_persona(entry)
                else:
                    continue
                if p is None:
                    continue
                self.personas[p.id] = p
        self._loaded = True

    def ensure_loaded(self) -> None:
        if not self._loaded:
            self.discover()

    def activate(self, persona_id: str) -> Persona | None:
        self.ensure_loaded()
        p = self.personas.get(persona_id)
        if p is None:
            return None
        self.active_id = persona_id
        return p

    def active(self) -> Persona | None:
        self.ensure_loaded()
        if self.active_id:
            return self.personas.get(self.active_id)
        return self.personas.get("nova-default")

    def list_all(self) -> list[Persona]:
        self.ensure_loaded()
        return list(self.personas.values())


_singleton: PersonaRegistry | None = None


def get_persona_registry() -> PersonaRegistry:
    global _singleton
    if _singleton is None:
        _singleton = PersonaRegistry()
        _singleton.ensure_loaded()
    return _singleton
