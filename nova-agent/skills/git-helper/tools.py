"""git-helper skill tools."""

from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

TOOLS = [
    {
        "name": "git_run",
        "description": (
            "Run a read-only git subcommand (status, log, diff, branch, show, remote, "
            "rev-parse, blame, ls-files, worktree list). Destructive verbs are blocked."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "subcommand": {"type": "string", "description": "git subcommand with args, e.g. 'log --oneline -10'"},
                "directory": {"type": "string", "description": "Repo directory", "default": "."},
            },
            "required": ["subcommand"],
        },
    },
    {
        "name": "git_smart_commit",
        "description": "Stage changes and commit with a structured message. Refuses to run if working tree is clean.",
        "input_schema": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Commit subject line (imperative, <72 chars)"},
                "body": {"type": "string", "description": "Optional commit body", "default": ""},
                "directory": {"type": "string", "default": "."},
                "paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific files to stage. If omitted, stages all tracked changes.",
                },
            },
            "required": ["message"],
        },
    },
    {
        "name": "git_pr_summary",
        "description": "Generate a PR-ready summary of commits on the current branch vs a base branch.",
        "input_schema": {
            "type": "object",
            "properties": {
                "base": {"type": "string", "description": "Base branch to diff against", "default": "main"},
                "directory": {"type": "string", "default": "."},
            },
        },
    },
]

_READONLY_VERBS = {
    "status", "log", "diff", "show", "branch", "remote", "rev-parse",
    "blame", "ls-files", "worktree", "config", "describe", "shortlog",
    "reflog", "stash", "tag",
}

_BLOCKED_FLAGS = ("--force", "-f", "--hard", "--no-verify", "--delete", "-D")


def _run(args: list[str], cwd: Path) -> tuple[int, str]:
    try:
        res = subprocess.run(
            ["git", *args], cwd=str(cwd), capture_output=True, text=True, timeout=30,
        )
        out = res.stdout
        if res.stderr:
            out += ("\n[stderr]: " + res.stderr if out else res.stderr)
        return res.returncode, out.strip()
    except FileNotFoundError:
        return 127, "git is not installed or not on PATH"
    except subprocess.TimeoutExpired:
        return 124, "git command timed out"


def execute(name: str, input_data: dict) -> str:
    directory = Path(input_data.get("directory", ".")).expanduser().resolve()
    if not directory.exists():
        return f"Error: {directory} does not exist"

    if name == "git_run":
        sub = input_data.get("subcommand", "").strip()
        if not sub:
            return "Error: empty subcommand"
        parts = shlex.split(sub)
        verb = parts[0] if parts else ""
        if verb not in _READONLY_VERBS:
            return f"Refused: '{verb}' is not in the read-only allowlist"
        for p in parts:
            if p in _BLOCKED_FLAGS:
                return f"Refused: flag '{p}' is blocked"
        code, out = _run(parts, directory)
        return out or f"(exit {code})"

    if name == "git_smart_commit":
        msg = input_data.get("message", "").strip()
        body = input_data.get("body", "").strip()
        paths = input_data.get("paths") or []
        if not msg:
            return "Error: commit message required"
        if len(msg) > 72:
            return f"Error: subject line too long ({len(msg)} > 72 chars)"

        code, status = _run(["status", "--porcelain"], directory)
        if code != 0:
            return f"git status failed: {status}"
        if not status:
            return "Working tree is clean — nothing to commit"

        if paths:
            _run(["add", "--", *paths], directory)
        else:
            _run(["add", "-u"], directory)

        full_msg = msg if not body else f"{msg}\n\n{body}"
        code, out = _run(["commit", "-m", full_msg], directory)
        return out or f"(exit {code})"

    if name == "git_pr_summary":
        base = input_data.get("base", "main")
        code, branch = _run(["rev-parse", "--abbrev-ref", "HEAD"], directory)
        if code != 0:
            return f"Not a git repo: {branch}"
        code, commits = _run(
            ["log", "--oneline", "--no-decorate", f"{base}..HEAD"], directory,
        )
        if code != 0:
            return f"git log failed: {commits}"
        code, stat = _run(["diff", "--stat", f"{base}...HEAD"], directory)
        return (
            f"Branch: {branch}\nBase: {base}\n\nCommits:\n{commits or '(none)'}\n\n"
            f"Diffstat:\n{stat or '(empty)'}"
        )

    return f"Unknown tool: {name}"
