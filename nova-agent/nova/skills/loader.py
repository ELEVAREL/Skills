"""SKILL.md parser and dynamic skill loader."""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import yaml


@dataclass
class Skill:
    """A loaded Nova skill."""

    name: str
    version: str
    description: str
    path: Path
    author: str = ""
    tags: list[str] = field(default_factory=list)
    triggers: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    personas: list[str] = field(default_factory=list)
    body: str = ""  # the markdown body after frontmatter
    tool_defs: list[dict] = field(default_factory=list)  # Anthropic-format tool schemas
    tool_executor: Callable[[str, dict], str] | None = None  # execute(name, input) -> str
    enabled: bool = True

    @property
    def id(self) -> str:
        return self.name.lower().replace(" ", "-")

    def tool_names(self) -> list[str]:
        return [t["name"] for t in self.tool_defs]

    def describe(self) -> str:
        lines = [f"{self.name} v{self.version} — {self.description}"]
        if self.tags:
            lines.append(f"  tags: {', '.join(self.tags)}")
        if self.tool_defs:
            lines.append(f"  tools: {', '.join(self.tool_names())}")
        if self.triggers:
            lines.append(f"  triggers: {', '.join(self.triggers)}")
        return "\n".join(lines)


def parse_skill_md(content: str) -> tuple[dict, str]:
    """Split a SKILL.md file into (frontmatter dict, markdown body).

    Frontmatter is a YAML block delimited by `---` at the top of the file.
    """
    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    try:
        frontmatter = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        frontmatter = {}
    body = parts[2].lstrip("\n")
    return frontmatter, body


def load_skill(skill_dir: Path) -> Skill | None:
    """Load a single skill from its directory. Returns None if invalid."""
    skill_dir = Path(skill_dir).expanduser().resolve()
    manifest = skill_dir / "SKILL.md"
    if not manifest.exists():
        return None

    try:
        content = manifest.read_text(encoding="utf-8")
    except OSError:
        return None

    frontmatter, body = parse_skill_md(content)
    name = frontmatter.get("name")
    if not name:
        return None

    skill = Skill(
        name=name,
        version=str(frontmatter.get("version", "0.0.1")),
        description=frontmatter.get("description", ""),
        path=skill_dir,
        author=frontmatter.get("author", ""),
        tags=list(frontmatter.get("tags") or []),
        triggers=list(frontmatter.get("triggers") or []),
        dependencies=list(frontmatter.get("dependencies") or []),
        personas=list(frontmatter.get("personas") or []),
        body=body,
    )

    # Load optional Python tool module
    tools_py = skill_dir / "tools.py"
    if tools_py.exists():
        try:
            mod = _import_isolated(f"nova_skill_{skill.id.replace('-', '_')}", tools_py)
            tool_defs = getattr(mod, "TOOLS", None)
            executor = getattr(mod, "execute", None)
            if isinstance(tool_defs, list):
                skill.tool_defs = tool_defs
            if callable(executor):
                skill.tool_executor = executor
        except Exception as e:
            # Don't crash registry over one broken skill — leave tools empty
            skill.description += f"  [load error: {e}]"

    return skill


def _import_isolated(module_name: str, file_path: Path) -> Any:
    """Import a Python file under a custom name without polluting sys.modules globally."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load spec for {file_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod
