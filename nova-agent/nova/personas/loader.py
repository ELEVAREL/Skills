"""SPIRIT.md parser and persona loader."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class Persona:
    """A Nova persona — a named AI personality with its own system prompt."""

    name: str
    version: str
    description: str
    path: Path
    system_prompt: str
    author: str = ""
    tags: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    model: str | None = None
    max_tokens: int | None = None
    temperature: float | None = None
    greeting: str = ""

    @property
    def id(self) -> str:
        return self.name.lower().replace(" ", "-")


def parse_spirit_md(content: str) -> tuple[dict, str]:
    """Split a SPIRIT.md file into (frontmatter, system prompt body)."""
    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    try:
        frontmatter = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        frontmatter = {}

    body = parts[2].strip()
    return frontmatter, body


def load_persona(persona_path: Path) -> Persona | None:
    """Load a persona from either a SPIRIT.md file or a directory containing one."""
    persona_path = Path(persona_path).expanduser().resolve()

    if persona_path.is_dir():
        manifest = persona_path / "SPIRIT.md"
    else:
        manifest = persona_path

    if not manifest.exists():
        return None

    try:
        content = manifest.read_text(encoding="utf-8")
    except OSError:
        return None

    frontmatter, body = parse_spirit_md(content)
    name = frontmatter.get("name")
    if not name or not body:
        return None

    return Persona(
        name=name,
        version=str(frontmatter.get("version", "0.0.1")),
        description=frontmatter.get("description", ""),
        path=manifest,
        system_prompt=body,
        author=frontmatter.get("author", ""),
        tags=list(frontmatter.get("tags") or []),
        skills=list(frontmatter.get("skills") or []),
        model=frontmatter.get("model"),
        max_tokens=frontmatter.get("max_tokens"),
        temperature=frontmatter.get("temperature"),
        greeting=frontmatter.get("greeting", ""),
    )
