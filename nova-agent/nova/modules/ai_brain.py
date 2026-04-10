"""AI brain module — Claude-powered natural language interface."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from nova.config import load_config, get_api_key
from nova.utils.display import console, ai_response, error, info, warning, ai_thinking, success

SYSTEM_PROMPT = """\
You are Nova, an AI assistant that lives in the user's terminal. You help organize files, \
manage their system, and automate tasks on their computer.

You have access to these tools to interact with the user's computer:

1. **run_command** — Execute a shell command and return the output
2. **list_files** — List files in a directory with details
3. **move_file** — Move a file from one location to another
4. **get_system_info** — Get system information (CPU, memory, disk)
5. **find_files** — Search for files by name pattern
6. **read_file** — Read the contents of a text file
7. **create_directory** — Create a new directory

Important rules:
- Always explain what you're doing before doing it
- For destructive operations (delete, overwrite), ask for confirmation first
- Be concise but helpful
- Show file operations as a summary, not verbose logs
- When organizing files, explain the categorization logic
- If you're unsure, ask the user rather than guessing
"""

TOOLS = [
    {
        "name": "run_command",
        "description": "Execute a shell command and return stdout/stderr. Use for system queries, package management, git operations, etc. Never run destructive commands without the user explicitly asking.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The shell command to execute"},
            },
            "required": ["command"],
        },
    },
    {
        "name": "list_files",
        "description": "List files in a directory with size, type, and modification date.",
        "input_schema": {
            "type": "object",
            "properties": {
                "directory": {"type": "string", "description": "Directory path to list"},
                "show_hidden": {"type": "boolean", "description": "Include hidden files", "default": False},
            },
            "required": ["directory"],
        },
    },
    {
        "name": "move_file",
        "description": "Move or rename a file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": "Source file path"},
                "destination": {"type": "string", "description": "Destination file path"},
            },
            "required": ["source", "destination"],
        },
    },
    {
        "name": "get_system_info",
        "description": "Get system information including CPU, memory, disk usage, and top processes.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "find_files",
        "description": "Search for files matching a pattern.",
        "input_schema": {
            "type": "object",
            "properties": {
                "directory": {"type": "string", "description": "Starting directory"},
                "pattern": {"type": "string", "description": "Filename pattern (glob)"},
            },
            "required": ["directory", "pattern"],
        },
    },
    {
        "name": "read_file",
        "description": "Read the contents of a text file (first 200 lines).",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to read"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "create_directory",
        "description": "Create a new directory (and parent directories if needed).",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path to create"},
            },
            "required": ["path"],
        },
    },
]


def execute_tool(name: str, input_data: dict) -> str:
    """Execute a tool and return the result."""
    try:
        if name == "run_command":
            result = subprocess.run(
                input_data["command"],
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(Path.home()),
            )
            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]: {result.stderr}"
            return output[:5000] or "(no output)"

        elif name == "list_files":
            directory = Path(input_data["directory"]).expanduser().resolve()
            if not directory.is_dir():
                return f"Error: {directory} is not a directory"
            files = []
            for entry in sorted(directory.iterdir()):
                if not input_data.get("show_hidden") and entry.name.startswith("."):
                    continue
                try:
                    stat = entry.stat()
                    size = stat.st_size
                    kind = "dir" if entry.is_dir() else entry.suffix or "file"
                    files.append(f"{'📁' if entry.is_dir() else '📄'} {entry.name:40s} {_humanize(size):>10s}  {kind}")
                except (PermissionError, OSError):
                    continue
            return "\n".join(files[:100]) or "(empty directory)"

        elif name == "move_file":
            src = Path(input_data["source"]).expanduser().resolve()
            dst = Path(input_data["destination"]).expanduser().resolve()
            if not src.exists():
                return f"Error: {src} does not exist"
            dst.parent.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.move(str(src), str(dst))
            return f"Moved {src.name} → {dst}"

        elif name == "get_system_info":
            from nova.modules.system import get_system_info, get_running_processes
            info_data = get_system_info()
            procs = get_running_processes(limit=10)
            result = "System Info:\n"
            for k, v in info_data.items():
                result += f"  {k}: {v}\n"
            result += "\nTop processes (by memory):\n"
            for p in procs:
                result += f"  {p['name']:30s} CPU:{p['cpu']:>6s}  MEM:{p['memory']:>6s}\n"
            return result

        elif name == "find_files":
            directory = Path(input_data["directory"]).expanduser().resolve()
            pattern = input_data["pattern"]
            matches = list(directory.rglob(pattern))[:50]
            return "\n".join(str(m) for m in matches) or "No files found"

        elif name == "read_file":
            filepath = Path(input_data["path"]).expanduser().resolve()
            if not filepath.is_file():
                return f"Error: {filepath} is not a file"
            lines = filepath.read_text(errors="replace").splitlines()[:200]
            return "\n".join(lines)

        elif name == "create_directory":
            dirpath = Path(input_data["path"]).expanduser().resolve()
            dirpath.mkdir(parents=True, exist_ok=True)
            return f"Created directory: {dirpath}"

        else:
            return f"Unknown tool: {name}"

    except Exception as e:
        return f"Error: {e}"


def _humanize(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


class AIBrain:
    """Claude-powered AI brain for Nova Agent."""

    def __init__(self):
        self.config = load_config()
        self.conversation: list[dict] = []
        self.client = None

    def _ensure_client(self):
        """Initialize the Anthropic client."""
        if self.client is not None:
            return True

        api_key = get_api_key()
        if not api_key:
            error("No API key found. Set ANTHROPIC_API_KEY environment variable.")
            error("  export ANTHROPIC_API_KEY=your-key-here")
            return False

        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
            return True
        except ImportError:
            error("anthropic package not installed. Run: pip install anthropic")
            return False

    def chat(self, user_message: str) -> str | None:
        """Send a message and get a response, handling tool calls."""
        if not self._ensure_client():
            return None

        self.conversation.append({"role": "user", "content": user_message})

        model = self.config["ai"]["model"]
        max_tokens = self.config["ai"]["max_tokens"]

        # Show thinking animation while waiting for API
        with ai_thinking() as progress:
            think_task = progress.add_task("Thinking", total=None)
            try:
                response = self.client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    system=SYSTEM_PROMPT,
                    tools=TOOLS,
                    messages=self.conversation,
                )
            except Exception as e:
                progress.stop()
                error(f"API error: {e}")
                self.conversation.pop()
                return None

        # Process the response — handle tool use loop
        return self._process_response(response, model, max_tokens)

    def _process_response(self, response, model: str, max_tokens: int) -> str | None:
        """Process API response, executing tools as needed."""
        assistant_content = response.content
        self.conversation.append({"role": "assistant", "content": assistant_content})

        # Collect text and tool results
        final_text = ""
        tool_results = []

        for block in assistant_content:
            if block.type == "text":
                final_text += block.text
            elif block.type == "tool_use":
                tool_name = block.name
                tool_input = block.input
                tool_id = block.id

                console.print(f"  [cyan]⚡ {tool_name}[/]([dim]{', '.join(f'{k}={v!r}' for k, v in tool_input.items())}[/])")
                result = execute_tool(tool_name, tool_input)
                success(f"{tool_name} complete")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": result,
                })

        # If there were tool calls, send results back
        if tool_results:
            self.conversation.append({"role": "user", "content": tool_results})

            with ai_thinking() as progress:
                progress.add_task("Processing results", total=None)
                try:
                    follow_up = self.client.messages.create(
                        model=model,
                        max_tokens=max_tokens,
                        system=SYSTEM_PROMPT,
                        tools=TOOLS,
                        messages=self.conversation,
                    )
                except Exception as e:
                    error(f"API error: {e}")
                    return final_text or None

            return self._process_response(follow_up, model, max_tokens)

        return final_text or None

    def reset(self):
        """Clear conversation history."""
        self.conversation = []
