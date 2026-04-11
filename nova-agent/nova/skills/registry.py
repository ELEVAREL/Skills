"""Skill registry — discovers skills across builtin and user directories."""

from __future__ import annotations

from pathlib import Path

from nova.skills.loader import Skill, load_skill

# Builtin skills ship with the Nova package
_PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
BUILTIN_SKILLS_DIR = _PACKAGE_ROOT / "skills"

# User skills live under ~/.nova/skills/
USER_SKILLS_DIR = Path.home() / ".nova" / "skills"


class SkillRegistry:
    """Loads and indexes all Nova skills from builtin + user directories."""

    def __init__(self):
        self.skills: dict[str, Skill] = {}
        self._loaded = False

    def discover(self, extra_dirs: list[Path] | None = None) -> None:
        """Scan all skill directories and load everything found."""
        self.skills.clear()

        search_dirs: list[Path] = []
        if BUILTIN_SKILLS_DIR.exists():
            search_dirs.append(BUILTIN_SKILLS_DIR)
        if USER_SKILLS_DIR.exists():
            search_dirs.append(USER_SKILLS_DIR)
        if extra_dirs:
            search_dirs.extend(extra_dirs)

        for base in search_dirs:
            for entry in sorted(base.iterdir()):
                if not entry.is_dir() or entry.name.startswith("."):
                    continue
                skill = load_skill(entry)
                if skill is None:
                    continue
                # Last-loaded wins — user skills override builtins by name
                self.skills[skill.id] = skill

        self._loaded = True

    def ensure_loaded(self) -> None:
        if not self._loaded:
            self.discover()

    def all_tools(self, persona_filter: str | None = None) -> list[dict]:
        """Return all tool schemas from enabled skills, optionally scoped to a persona."""
        self.ensure_loaded()
        out: list[dict] = []
        for skill in self.skills.values():
            if not skill.enabled:
                continue
            if persona_filter and skill.personas and persona_filter not in skill.personas:
                continue
            out.extend(skill.tool_defs)
        return out

    def find_tool(self, tool_name: str) -> Skill | None:
        """Return the skill that owns a given tool name."""
        self.ensure_loaded()
        for skill in self.skills.values():
            if tool_name in skill.tool_names():
                return skill
        return None

    def enable(self, skill_id: str) -> bool:
        self.ensure_loaded()
        s = self.skills.get(skill_id)
        if s:
            s.enabled = True
            return True
        return False

    def disable(self, skill_id: str) -> bool:
        self.ensure_loaded()
        s = self.skills.get(skill_id)
        if s:
            s.enabled = False
            return True
        return False

    def search(self, query: str) -> list[Skill]:
        """Keyword search across name, description, tags, triggers."""
        self.ensure_loaded()
        q = query.lower()
        hits: list[Skill] = []
        for s in self.skills.values():
            blob = " ".join([s.name, s.description, " ".join(s.tags), " ".join(s.triggers)]).lower()
            if q in blob:
                hits.append(s)
        return hits


_singleton: SkillRegistry | None = None


def get_registry() -> SkillRegistry:
    global _singleton
    if _singleton is None:
        _singleton = SkillRegistry()
        _singleton.ensure_loaded()
    return _singleton
