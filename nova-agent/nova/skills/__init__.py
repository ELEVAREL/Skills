"""Nova Skill system — plugin architecture for extending Nova's capabilities.

A Skill is a directory with a SKILL.md manifest (YAML frontmatter + markdown body)
and optional Python tool modules. Skills are Nova's answer to OpenClaw's ClawHub —
shareable, composable units of capability.

Directory layout:
    my-skill/
        SKILL.md          # YAML frontmatter + docs
        tools.py          # optional — exposes TOOLS list and execute(name, input)
        resources/        # optional — any static files

SKILL.md frontmatter fields:
    name: string                (required)
    version: string             (required)
    description: string         (required)
    author: string              (optional)
    tags: [string]              (optional)
    tools: [string]             (optional — names of tools this skill adds)
    triggers: [string]          (optional — keywords that activate this skill)
    dependencies: [string]      (optional — other skill names)
    personas: [string]          (optional — which personas load this by default)
"""

from nova.skills.loader import Skill, load_skill, parse_skill_md
from nova.skills.registry import SkillRegistry, get_registry

__all__ = ["Skill", "load_skill", "parse_skill_md", "SkillRegistry", "get_registry"]
