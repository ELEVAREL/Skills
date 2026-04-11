"""AI brain module — Claude-powered natural language interface."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from nova.config import load_config, get_api_key
from nova.utils.display import console, ai_response, error, info, warning, ai_thinking, success

BASE_SYSTEM_PROMPT = """\
You are Nova, an AI agent that lives in the user's terminal. You help organize files, \
manage their system, automate tasks, and run skills across channels.

Core rules:
- Call tools to answer questions; don't guess state of the machine.
- Before destructive operations (delete, overwrite, kill, push), state the plan and wait.
- Be concise. Show results before explanations.
- Skills provide domain-specific tools. Prefer a skill tool over raw shell when both exist.
- When the user asks you to remember something across sessions, use the memory_* tools.
"""

# Legacy name retained for back-compat
SYSTEM_PROMPT = BASE_SYSTEM_PROMPT

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
    {
        "name": "organize_files",
        "description": "Organize files in a directory by categorizing them into folders (Documents, Images, Code, etc.). Returns a plan of what would be moved.",
        "input_schema": {
            "type": "object",
            "properties": {
                "directory": {"type": "string", "description": "Directory to organize"},
                "execute": {"type": "boolean", "description": "Actually move files (true) or just preview (false)", "default": False},
            },
            "required": ["directory"],
        },
    },
    {
        "name": "analyze_directory",
        "description": "Analyze a directory for file statistics, categories, largest files, duplicates, and old files.",
        "input_schema": {
            "type": "object",
            "properties": {
                "directory": {"type": "string", "description": "Directory to analyze"},
            },
            "required": ["directory"],
        },
    },
    {
        "name": "check_network",
        "description": "Check network connectivity, scan ports, or get bandwidth info.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["connectivity", "ports", "bandwidth", "interfaces"], "description": "Network check type"},
                "host": {"type": "string", "description": "Host for port scan (default: localhost)"},
            },
            "required": ["action"],
        },
    },
    {
        "name": "git_status",
        "description": "Get git repository status, find all repos, or show git statistics.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["status", "find_repos", "stats"], "description": "Git action"},
                "directory": {"type": "string", "description": "Repository or search directory"},
            },
            "required": ["action"],
        },
    },
    {
        "name": "search_content",
        "description": "Search for text patterns inside files (like grep).",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Text pattern to search for"},
                "directory": {"type": "string", "description": "Directory to search in"},
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "find_duplicates",
        "description": "Find duplicate files by content hash in a directory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "directory": {"type": "string", "description": "Directory to scan for duplicates"},
            },
            "required": ["directory"],
        },
    },
    {
        "name": "manage_notes",
        "description": "Add, list, or search quick notes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["add", "list", "search"], "description": "Note action"},
                "content": {"type": "string", "description": "Note content (for add) or search query"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags for the note"},
            },
            "required": ["action"],
        },
    },
    {
        "name": "analyze_code",
        "description": "Perform a full codebase analysis: languages, line counts, TODOs, security flags, large functions, test coverage estimate.",
        "input_schema": {
            "type": "object",
            "properties": {
                "directory": {"type": "string", "description": "Directory to analyze", "default": "."},
            },
        },
    },
    {
        "name": "scaffold_project",
        "description": "Create a new project from a template. Templates: python, node, react, api.",
        "input_schema": {
            "type": "object",
            "properties": {
                "template": {"type": "string", "enum": ["python", "node", "react", "api"]},
                "name": {"type": "string", "description": "Project name"},
                "directory": {"type": "string", "description": "Parent directory", "default": "."},
            },
            "required": ["template", "name"],
        },
    },
    {
        "name": "manage_packages",
        "description": "List packages, detect package managers, or check for outdated dependencies.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["list", "detect", "outdated"]},
                "directory": {"type": "string", "description": "Project directory", "default": "."},
            },
            "required": ["action"],
        },
    },
    {
        "name": "manage_services",
        "description": "Find dev servers, listening ports, resource hogs, or kill processes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["dev_servers", "listeners", "hogs", "kill_pid", "kill_port"]},
                "target": {"type": "integer", "description": "PID or port number (for kill actions)"},
            },
            "required": ["action"],
        },
    },
    {
        "name": "memory_remember",
        "description": (
            "Save a persistent memory that will be available in future sessions. "
            "Types: user (about the user), feedback (behavior rules), project (ongoing work), "
            "reference (pointers to external systems), fact (general facts)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["user", "feedback", "project", "reference", "fact"]},
                "title": {"type": "string", "description": "Short title"},
                "body": {"type": "string", "description": "Full memory content"},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["type", "title", "body"],
        },
    },
    {
        "name": "memory_recall",
        "description": "Search persistent memory across all stored memories by keyword.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "default": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "memory_list",
        "description": "List recent memories, optionally filtered by type.",
        "input_schema": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["user", "feedback", "project", "reference", "fact"]},
                "limit": {"type": "integer", "default": 20},
            },
        },
    },
    {
        "name": "memory_forget",
        "description": "Delete a memory by its id. Requires explicit user confirmation upstream.",
        "input_schema": {
            "type": "object",
            "properties": {"id": {"type": "integer"}},
            "required": ["id"],
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

        elif name == "organize_files":
            from nova.modules.organizer import organize_files
            actions = organize_files(
                input_data["directory"],
                dry_run=not input_data.get("execute", False),
            )
            mode = "EXECUTED" if input_data.get("execute") else "DRY RUN"
            lines = [f"Organization plan ({mode}):"]
            for a in actions[:30]:
                lines.append(f"  {a['name']} ({a.get('size_human','')}) — {a.get('action','')}")
            moved = sum(1 for a in actions if "→" in a.get("action", ""))
            lines.append(f"\nTotal: {len(actions)} files, {moved} would be moved")
            return "\n".join(lines)

        elif name == "analyze_directory":
            from nova.modules.organizer import analyze_directory, humanize_size
            stats = analyze_directory(input_data["directory"])
            lines = [f"Directory Analysis:"]
            lines.append(f"  Total files: {stats['total_files']}")
            lines.append(f"  Total size: {stats['total_size']}")
            lines.append(f"  Categories:")
            for cat, data in sorted(stats["categories"].items(), key=lambda x: x[1]["size"], reverse=True):
                lines.append(f"    {cat}: {data['count']} files ({humanize_size(data['size'])})")
            if stats["duplicates"]:
                lines.append(f"  Duplicates: {len(stats['duplicates'])} files with same names")
            if stats["old_files"]:
                lines.append(f"  Old files (90+ days): {len(stats['old_files'])}")
            return "\n".join(lines)

        elif name == "check_network":
            action = input_data["action"]
            if action == "connectivity":
                from nova.modules.network import check_connectivity
                results = check_connectivity()
                return "\n".join(f"  {k}: {v}" for k, v in results.items())
            elif action == "ports":
                from nova.modules.network import scan_ports
                results = scan_ports(input_data.get("host", "localhost"))
                open_ports = [r for r in results if r["status"] == "open"]
                return "\n".join(f"  Port {r['port']}: OPEN ({r['service']})" for r in open_ports) or "No open ports"
            elif action == "bandwidth":
                from nova.modules.network import get_bandwidth
                bw = get_bandwidth()
                return "\n".join(f"  {k}: {v}" for k, v in bw.items())
            elif action == "interfaces":
                from nova.modules.network import get_network_info
                info_data = get_network_info()
                return "\n".join(f"  {k}: {v.get('ipv4', 'N/A')} ({v['status']})" for k, v in info_data.items())
            return "Unknown network action"

        elif name == "git_status":
            action = input_data["action"]
            directory = input_data.get("directory", ".")
            if action == "status":
                from nova.modules.git_manager import get_repo_status
                s = get_repo_status(directory)
                return f"Repo: {s['name']}\nBranch: {s['branch']}\nChanges: {s['changes']}\nLast commit: {s['last_commit']}"
            elif action == "find_repos":
                from nova.modules.git_manager import find_repos
                repos = find_repos(directory)
                return f"Found {len(repos)} repos:\n" + "\n".join(f"  {r}" for r in repos[:20])
            elif action == "stats":
                from nova.modules.git_manager import get_repo_status
                s = get_repo_status(directory)
                return f"Repo: {s['name']}, Branch: {s['branch']}, Uncommitted: {s['changes']}, Ahead: {s['ahead']}, Behind: {s['behind']}"
            return "Unknown git action"

        elif name == "search_content":
            from nova.modules.search import search_content
            results = search_content(input_data["pattern"], input_data.get("directory", "."))
            if not results:
                return "No matches found"
            return "\n".join(f"  {r['file']}: {r['match']}" for r in results[:20])

        elif name == "find_duplicates":
            from nova.modules.duplicates import find_duplicates
            dupes = find_duplicates(input_data["directory"])
            if not dupes:
                return "No duplicate files found"
            lines = [f"Found {len(dupes)} duplicate groups:"]
            for d in dupes[:10]:
                lines.append(f"  {d['count']} copies of {d['size_each']} file ({d['wasted']} wasted):")
                for f in d["files"][:3]:
                    lines.append(f"    {f}")
            return "\n".join(lines)

        elif name == "manage_notes":
            action = input_data["action"]
            if action == "add":
                from nova.modules.notes import add_note
                add_note(input_data.get("content", ""), input_data.get("tags", []))
                return "Note saved"
            elif action == "list":
                from nova.modules.notes import _load_json, NOTES_FILE
                notes = _load_json(NOTES_FILE)
                if not notes:
                    return "No notes"
                return "\n".join(f"  #{n['id']}: {n['content'][:80]}" for n in notes[-20:])
            elif action == "search":
                from nova.modules.notes import search_notes
                results = search_notes(input_data.get("content", ""))
                return "\n".join(f"  #{n['id']}: {n['content'][:80]}" for n in results) or "No matches"
            return "Unknown note action"

        elif name == "analyze_code":
            from nova.modules.code_analyzer import analyze_codebase
            results = analyze_codebase(input_data.get("directory", "."))
            total_files = sum(results["file_counts"].values())
            total_lines = sum(results["line_counts"].values())
            lines = [f"Codebase Analysis:"]
            lines.append(f"  Total files: {total_files:,}")
            lines.append(f"  Total lines: {total_lines:,}")
            lines.append(f"  Languages: {len(results['languages'])}")
            lines.append(f"  Top languages:")
            for lang, count in results["line_counts"].most_common(5):
                lines.append(f"    {lang}: {count:,} lines")
            lines.append(f"  TODO/FIXME markers: {len(results['todos'])}")
            lines.append(f"  Security flags: {len(results['security_flags'])}")
            lines.append(f"  Large functions: {len(results['large_functions'])}")
            tc = results["test_coverage"]
            ratio = (tc["test_files"] / max(1, tc["source_files"])) * 100
            lines.append(f"  Test ratio: {ratio:.0f}% ({tc['test_files']} test files)")
            if results["security_flags"]:
                lines.append("\n  Top security issues:")
                for s in results["security_flags"][:5]:
                    lines.append(f"    {s['file']}:{s['line']}  {s['issue']}")
            return "\n".join(lines)

        elif name == "scaffold_project":
            from nova.modules.scaffolder import scaffold_project
            scaffold_project(
                input_data["template"],
                input_data["name"],
                input_data.get("directory", "."),
            )
            return f"Project '{input_data['name']}' scaffolded from '{input_data['template']}' template"

        elif name == "manage_packages":
            action = input_data["action"]
            directory = input_data.get("directory", ".")
            if action == "list":
                from nova.modules.packages import list_packages
                pkgs = list_packages(directory)
                if not pkgs:
                    return "No packages found"
                lines = []
                for pm, data in pkgs.items():
                    lines.append(f"{pm}: {data['total']} packages")
                    for pkg_name in list(data.get("dependencies", {}).keys())[:10]:
                        lines.append(f"  {pkg_name}")
                return "\n".join(lines)
            elif action == "detect":
                from nova.modules.packages import detect_package_manager
                managers = detect_package_manager(directory)
                if not managers:
                    return "No package managers detected"
                return "\n".join(f"{pm}: {d['config']}" for pm, d in managers.items())
            elif action == "outdated":
                from nova.modules.packages import check_outdated
                check_outdated(directory)
                return "Outdated check complete (see output above)"
            return "Unknown package action"

        elif name == "manage_services":
            action = input_data["action"]
            if action == "dev_servers":
                from nova.modules.services import find_dev_servers
                servers = find_dev_servers()
                if not servers:
                    return "No development servers running"
                lines = [f"Found {len(servers)} dev servers:"]
                for s in servers:
                    ports = ",".join(str(p) for p in s["ports"]) or "?"
                    lines.append(f"  PID {s['pid']}: {s['category']} on port(s) {ports}")
                return "\n".join(lines)
            elif action == "listeners":
                from nova.modules.services import find_listening_ports
                listeners = find_listening_ports()
                return "\n".join(f"Port {l['port']}: {l['name']} (PID {l['pid']})" for l in listeners[:30])
            elif action == "hogs":
                import psutil
                procs = sorted(
                    [p.info for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"])],
                    key=lambda p: (p.get("cpu_percent") or 0) + (p.get("memory_percent") or 0),
                    reverse=True,
                )[:10]
                return "\n".join(
                    f"PID {p['pid']}: {p.get('name','?')} CPU:{p.get('cpu_percent',0):.1f}% MEM:{p.get('memory_percent',0):.1f}%"
                    for p in procs
                )
            elif action == "kill_pid":
                from nova.modules.services import kill_process
                kill_process(input_data["target"])
                return f"Killed PID {input_data['target']}"
            elif action == "kill_port":
                from nova.modules.services import kill_port
                kill_port(input_data["target"])
                return f"Killed process on port {input_data['target']}"
            return "Unknown service action"

        elif name == "memory_remember":
            from nova.modules.memory import remember
            mid = remember(
                input_data["type"],
                input_data["title"],
                input_data["body"],
                input_data.get("tags") or [],
            )
            return f"Remembered #{mid}: {input_data['title']}"

        elif name == "memory_recall":
            from nova.modules.memory import recall
            results = recall(input_data["query"], int(input_data.get("limit", 10)))
            if not results:
                return "No memories matched."
            lines = [f"Found {len(results)} memories:"]
            for r in results:
                tags = f" [{', '.join(r['tags'])}]" if r["tags"] else ""
                lines.append(f"  #{r['id']} ({r['type']}){tags} {r['title']}: {r['body'][:160]}")
            return "\n".join(lines)

        elif name == "memory_list":
            from nova.modules.memory import list_memories
            results = list_memories(input_data.get("type"), int(input_data.get("limit", 20)))
            if not results:
                return "No memories stored."
            lines = [f"{len(results)} memories:"]
            for r in results:
                lines.append(f"  #{r['id']} ({r['type']}) {r['title']}")
            return "\n".join(lines)

        elif name == "memory_forget":
            from nova.modules.memory import forget
            ok = forget(int(input_data["id"]))
            return f"Deleted memory #{input_data['id']}" if ok else f"No memory with id {input_data['id']}"

        # Dynamic skill tool dispatch
        from nova.skills import get_registry
        owning_skill = get_registry().find_tool(name)
        if owning_skill and owning_skill.tool_executor:
            return owning_skill.tool_executor(name, input_data)

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
    """Claude-powered AI brain for Nova Agent.

    Accepts a persona_id; merges that persona's system prompt + memory context +
    core tools + dynamic skill tools on every turn so skills installed mid-session
    become available without a restart.
    """

    def __init__(self, persona_id: str | None = None):
        self.config = load_config()
        self.conversation: list[dict] = []
        self.client = None
        self._persona_id = persona_id
        # Activate the persona up front so greetings etc. can reference it
        if persona_id:
            try:
                from nova.personas import get_persona_registry
                get_persona_registry().activate(persona_id)
            except Exception:
                pass

    def _active_persona(self):
        try:
            from nova.personas import get_persona_registry
            reg = get_persona_registry()
            if self._persona_id:
                return reg.personas.get(self._persona_id) or reg.active()
            return reg.active()
        except Exception:
            return None

    def _build_system_prompt(self) -> str:
        parts = [BASE_SYSTEM_PROMPT]
        persona = self._active_persona()
        if persona:
            parts.append(f"## Persona: {persona.name}\n{persona.system_prompt}")

        try:
            from nova.modules.memory import get_store
            mem_block = get_store().recent_context(limit=6)
            if mem_block:
                parts.append(mem_block)
        except Exception:
            pass

        return "\n\n".join(parts)

    def _build_tools(self) -> list[dict]:
        """Merge core tools with enabled skill tools."""
        tools: list[dict] = list(TOOLS)
        seen = {t["name"] for t in tools}
        try:
            from nova.skills import get_registry
            for skill_tool in get_registry().all_tools():
                if skill_tool["name"] not in seen:
                    tools.append(skill_tool)
                    seen.add(skill_tool["name"])
        except Exception:
            pass
        return tools

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

        persona = self._active_persona()
        model = (persona.model if persona and persona.model else self.config["ai"]["model"])
        max_tokens = (persona.max_tokens if persona and persona.max_tokens else self.config["ai"]["max_tokens"])
        system_prompt = self._build_system_prompt()
        tools = self._build_tools()

        # Show thinking animation while waiting for API
        with ai_thinking() as progress:
            think_task = progress.add_task("Thinking", total=None)
            try:
                response = self.client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    system=system_prompt,
                    tools=tools,
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
                        system=self._build_system_prompt(),
                        tools=self._build_tools(),
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
