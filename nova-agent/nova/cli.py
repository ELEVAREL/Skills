"""Nova Agent CLI — main entry point."""

import sys
import click
from pathlib import Path

from nova.utils.display import (
    console, banner, welcome_dashboard, success, error, warning, info, muted, ai_response,
)


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    """Nova — AI-powered CLI agent for organizing your computer."""
    if ctx.invoked_subcommand is None:
        # Launch interactive mode
        interactive_mode()


# ─── Interactive Mode ───────────────────────────────────────────────

def interactive_mode():
    """Launch the interactive Nova shell."""
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.styles import Style

    from nova.config import ensure_config_dir, DEFAULT_CONFIG_DIR
    from nova.modules.ai_brain import AIBrain
    from nova.modules.productivity import track_session_start, track_command

    banner()
    welcome_dashboard()

    ensure_config_dir()
    track_session_start()
    history_file = DEFAULT_CONFIG_DIR / "history"

    # Warm up the skill + persona registries so the first message is snappy
    try:
        from nova.skills import get_registry as _get_skills
        from nova.personas import get_persona_registry as _get_personas
        _get_skills()
        _get_personas()
    except Exception:
        pass

    style = Style.from_dict({
        "prompt": "#7b68ee bold",
        "prompt.arrow": "#00d4ff bold",
    })

    session = PromptSession(
        history=FileHistory(str(history_file)),
        auto_suggest=AutoSuggestFromHistory(),
        style=style,
    )

    brain = AIBrain()

    while True:
        try:
            user_input = session.prompt(
                [("class:prompt.arrow", "◆ "), ("class:prompt", "nova "), ("class:prompt.arrow", "› ")],
            ).strip()

            if not user_input:
                continue

            track_command()

            # Handle slash commands
            if user_input.startswith("/"):
                handled = handle_slash_command(user_input, brain)
                if handled == "quit":
                    break
                continue

            # Send to AI brain
            response = brain.chat(user_input)
            if response:
                ai_response(response)

        except KeyboardInterrupt:
            console.print()
            continue
        except EOFError:
            break

    console.print("\n[dim]Goodbye![/]")


def handle_slash_command(command: str, brain) -> str | None:
    """Handle slash commands in interactive mode."""
    parts = command.split(maxsplit=1)
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    if cmd in ("/quit", "/exit", "/q"):
        return "quit"

    elif cmd == "/help":
        from rich.table import Table
        from nova.utils.display import section_header

        sections = {
            "Files": {
                "/organize <dir>": "Organize files into categorized folders",
                "/analyze <dir>": "Analyze directory statistics",
                "/watch <dir>": "Auto-organize new files",
                "/large [dir]": "Find large files",
                "/duplicates [dir]": "Find duplicates by content hash",
            },
            "Search": {
                "/find <name>": "Search files by name",
                "/grep <pattern>": "Search file contents",
                "/recent [dir]": "Recently modified files",
            },
            "Code": {
                "/code [dir]": "Full codebase analysis (security + debt + complexity)",
                "/scaffold <template> <name>": "Create new project from template",
                "/scaffold list": "Show available templates",
                "/packages": "List installed packages",
                "/outdated": "Check for outdated packages",
                "/pm-detect": "Detect package managers in use",
            },
            "Services": {
                "/dev-servers": "Find running dev servers",
                "/listeners": "Show all listening ports",
                "/hogs": "Show top CPU/memory consumers",
                "/kill-pid <pid>": "Kill a process by PID",
                "/kill-port <port>": "Kill process on a port",
            },
            "Productivity": {
                "/dashboard": "Live system monitor (like htop)",
                "/stats": "Productivity stats and streak",
            },
            "System": {
                "/system": "Full system information",
                "/processes": "Top processes by resource usage",
                "/disks": "Disk usage across partitions",
                "/cleanup": "Find cleanup opportunities",
            },
            "Network": {
                "/network": "Network interface info",
                "/ping": "Test connectivity to major services",
                "/ports [host]": "Scan open ports",
                "/bandwidth": "Current network bandwidth",
                "/ip": "Show public IP address",
            },
            "Git": {
                "/repos [dir]": "Find and show all git repos",
                "/git": "Current repo status",
                "/git-stats": "Repository statistics",
            },
            "Productivity": {
                "/note <text>": "Save a quick note",
                "/notes": "View saved notes",
                "/bookmark <path>": "Bookmark a file or directory",
                "/bookmarks": "View saved bookmarks",
                "/remind <msg> <min>": "Set a reminder",
                "/timer <sec> [label]": "Start a countdown timer",
                "/pomodoro": "Start a Pomodoro work session",
            },
            "Clipboard": {
                "/clip save": "Save clipboard to history",
                "/clip list": "View clipboard history",
                "/clip paste <n>": "Restore item from history",
                "/clip search <q>": "Search clipboard history",
            },
            "Environment": {
                "/dotfiles": "List your dotfiles",
                "/dotfiles backup": "Backup all dotfiles",
                "/aliases": "Show shell aliases",
                "/env [PREFIX]": "Show environment variables",
            },
            "Personas & Skills": {
                "/persona list": "List available personas",
                "/persona use <id>": "Switch active persona",
                "/skills list": "List loaded skills",
                "/skills reload": "Rescan skill directories",
                "/skills enable/disable <id>": "Toggle a skill",
                "/hub refresh": "Refresh hub index",
                "/hub install <id>": "Install skill from hub",
            },
            "Memory": {
                "/mem list": "Recent memories",
                "/mem add <type> <title>::<body>": "Save a memory",
                "/mem recall <query>": "Search memories",
                "/mem forget <id>": "Delete a memory",
            },
            "Gateway": {
                "/gateway start": "Start Nova gateway (HTTP API)",
                "/gateway stop": "Stop gateway",
                "/gateway status": "Check gateway health",
            },
            "Session": {
                "/clear": "Clear AI conversation history",
                "/config": "Show current configuration",
                "/help": "Show this help",
                "/quit": "Exit Nova",
            },
        }

        console.print()
        for section_name, commands in sections.items():
            table = Table(title=f"[bold]{section_name}[/]", show_lines=False,
                         border_style="dim cyan", header_style="bold cyan",
                         title_style="bold magenta")
            table.add_column("Command", style="cyan", min_width=25)
            table.add_column("Description", style="white")
            for c, desc in commands.items():
                table.add_row(c, desc)
            console.print(table)
            console.print()

        muted("Or just type naturally — Nova AI understands plain English!")
        console.print()

    elif cmd == "/organize":
        target = args or "."
        ctx = click.Context(organize)
        ctx.invoke(organize, directory=target, dry_run=True)

    elif cmd == "/analyze":
        target = args or "."
        ctx = click.Context(analyze)
        ctx.invoke(analyze, directory=target)

    elif cmd == "/watch":
        target = args or str(Path.home() / "Downloads")
        ctx = click.Context(watch)
        ctx.invoke(watch, directory=target, dry_run=True)

    elif cmd == "/system":
        ctx = click.Context(system)
        ctx.invoke(system)

    elif cmd == "/processes":
        from nova.modules.system import show_processes
        show_processes()

    elif cmd == "/disks":
        from nova.modules.system import show_disk_usage
        show_disk_usage()

    elif cmd == "/large":
        target = args or str(Path.home())
        from nova.modules.system import find_large_files
        from nova.utils.display import file_table
        files = find_large_files(target, min_size_mb=50, limit=20)
        if files:
            display_files = [
                {"name": f["name"], "size_human": f["size_human"],
                 "category": f["modified"], "action": f["path"]}
                for f in files
            ]
            console.print(file_table(display_files, title="Large Files"))
        else:
            info("No large files found (>50MB)")

    elif cmd == "/cleanup":
        from nova.modules.system import cleanup_suggestions
        suggestions = cleanup_suggestions()
        console.print()
        info(f"Trash: {suggestions['trash']}")
        if suggestions["caches"]:
            console.print()
            from rich.table import Table
            table = Table(title="Caches")
            table.add_column("Cache", style="cyan")
            table.add_column("Size", style="yellow", justify="right")
            for c in suggestions["caches"]:
                table.add_row(c["name"], c["size"])
            console.print(table)
        if suggestions["large_files"]:
            console.print()
            info(f"Found {len(suggestions['large_files'])} files >500MB")
        info(f"Temp files: {suggestions['temp_files']}")
        console.print()

    # ─── Code Analysis ───────────────────────────────────────────
    elif cmd == "/code":
        from nova.modules.code_analyzer import show_codebase_analysis
        show_codebase_analysis(args or ".")

    elif cmd == "/scaffold":
        from nova.modules.scaffolder import scaffold_project, list_templates
        if args == "list" or not args:
            list_templates()
        else:
            parts = args.split(maxsplit=1)
            if len(parts) == 2:
                scaffold_project(parts[0], parts[1])
            else:
                warning("Usage: /scaffold <template> <name>")

    elif cmd in ("/packages", "/pkgs"):
        from nova.modules.packages import show_packages
        show_packages(args or ".")

    elif cmd == "/outdated":
        from nova.modules.packages import check_outdated
        check_outdated(args or ".")

    elif cmd == "/pm-detect":
        from nova.modules.packages import show_detected
        show_detected(args or ".")

    # ─── Services ────────────────────────────────────────────────
    elif cmd == "/dev-servers":
        from nova.modules.services import show_dev_servers
        show_dev_servers()

    elif cmd == "/listeners":
        from nova.modules.services import show_listeners
        show_listeners()

    elif cmd == "/hogs":
        from nova.modules.services import show_resource_hogs
        show_resource_hogs()

    elif cmd == "/kill-pid":
        from nova.modules.services import kill_process
        if args.isdigit():
            kill_process(int(args))
        else:
            warning("Usage: /kill-pid <pid>")

    elif cmd == "/kill-port":
        from nova.modules.services import kill_port
        if args.isdigit():
            kill_port(int(args))
        else:
            warning("Usage: /kill-port <port>")

    # ─── Productivity ────────────────────────────────────────────
    elif cmd == "/dashboard":
        from nova.modules.dashboard import run_dashboard
        run_dashboard()

    elif cmd == "/stats":
        from nova.modules.productivity import show_stats
        show_stats()

    # ─── Network ─────────────────────────────────────────────────
    elif cmd == "/ping":
        from nova.modules.network import show_connectivity
        show_connectivity()

    elif cmd == "/network":
        from nova.modules.network import show_network_info
        show_network_info()

    elif cmd == "/ports":
        from nova.modules.network import show_ports
        show_ports(args or "localhost")

    elif cmd == "/bandwidth":
        from nova.modules.network import get_bandwidth
        from nova.utils.display import summary_panel
        bw = get_bandwidth()
        summary_panel("Network Bandwidth", {
            "Download": bw["download_speed"],
            "Upload": bw["upload_speed"],
            "Total Received": bw["total_received"],
            "Total Sent": bw["total_sent"],
        })

    elif cmd == "/ip":
        from nova.modules.network import get_public_ip
        ip = get_public_ip()
        if ip:
            info(f"Public IP: [bold]{ip}[/]")
        else:
            error("Could not determine public IP")

    # ─── Git ───────────────────────────────────────────────────
    elif cmd == "/repos":
        from nova.modules.git_manager import show_all_repos
        show_all_repos(args or "~", max_depth=3)

    elif cmd == "/git":
        from nova.modules.git_manager import show_repo_status
        show_repo_status(args or ".")

    elif cmd in ("/git-stats", "/gitstats"):
        from nova.modules.git_manager import show_git_stats
        show_git_stats(args or ".")

    # ─── Search ────────────────────────────────────────────────
    elif cmd == "/find":
        if not args:
            warning("Usage: /find <filename>")
        else:
            from nova.modules.search import show_file_search
            show_file_search(args)

    elif cmd == "/grep":
        if not args:
            warning("Usage: /grep <pattern>")
        else:
            from nova.modules.search import show_content_search
            show_content_search(args)

    elif cmd == "/recent":
        from nova.modules.search import show_recent
        show_recent(args or ".", hours=24)

    elif cmd == "/duplicates":
        from nova.modules.duplicates import show_duplicates
        show_duplicates(args or ".")

    # ─── Notes & Bookmarks ─────────────────────────────────────
    elif cmd == "/note":
        if not args:
            warning("Usage: /note <text>")
        else:
            from nova.modules.notes import add_note
            # Parse tags with #tag syntax
            words = args.split()
            tags = [w[1:] for w in words if w.startswith("#")]
            text = " ".join(w for w in words if not w.startswith("#"))
            add_note(text, tags)

    elif cmd == "/notes":
        from nova.modules.notes import show_notes
        show_notes(tag_filter=args if args else None)

    elif cmd == "/bookmark":
        if not args:
            warning("Usage: /bookmark <path> [label]")
        else:
            from nova.modules.notes import add_bookmark
            parts = args.split(maxsplit=1)
            add_bookmark(parts[0], parts[1] if len(parts) > 1 else None)

    elif cmd == "/bookmarks":
        from nova.modules.notes import show_bookmarks
        show_bookmarks()

    # ─── Scheduler ─────────────────────────────────────────────
    elif cmd == "/remind":
        if not args:
            warning("Usage: /remind <message> <minutes>")
        else:
            parts = args.rsplit(maxsplit=1)
            if len(parts) == 2 and parts[1].isdigit():
                from nova.modules.scheduler import add_reminder
                add_reminder(parts[0], int(parts[1]))
            else:
                warning("Usage: /remind <message> <minutes>")

    elif cmd == "/timer":
        if not args:
            warning("Usage: /timer <seconds> [label]")
        else:
            parts = args.split(maxsplit=1)
            if parts[0].isdigit():
                from nova.modules.scheduler import add_timer
                add_timer(parts[1] if len(parts) > 1 else "Timer", int(parts[0]))
            else:
                warning("Usage: /timer <seconds> [label]")

    elif cmd == "/pomodoro":
        from nova.modules.scheduler import pomodoro
        pomodoro()

    elif cmd == "/tasks":
        from nova.modules.scheduler import show_tasks
        show_tasks()

    # ─── Clipboard ─────────────────────────────────────────────
    elif cmd == "/clip":
        subcmd = args.split(maxsplit=1)
        sub = subcmd[0] if subcmd else "list"
        sub_args = subcmd[1] if len(subcmd) > 1 else ""

        from nova.modules import clipboard
        if sub == "save":
            clipboard.capture_clipboard()
        elif sub == "list":
            clipboard.show_history()
        elif sub == "paste" and sub_args.isdigit():
            clipboard.paste_from_history(int(sub_args))
        elif sub == "search" and sub_args:
            results = clipboard.search_history(sub_args)
            if results:
                info(f"Found {len(results)} matches")
                for r in results[:10]:
                    console.print(f"  [dim]{r['preview']}[/]")
            else:
                info("No matches")
        elif sub == "clear":
            clipboard.clear_history()
        else:
            warning("Usage: /clip [save|list|paste <n>|search <query>|clear]")

    # ─── Dotfiles & Environment ────────────────────────────────
    elif cmd == "/dotfiles":
        from nova.modules import dotfiles
        if args == "backup":
            dotfiles.backup_dotfiles()
        elif args == "backups":
            dotfiles.list_backups()
        else:
            dotfiles.show_dotfiles()

    elif cmd == "/aliases":
        from nova.modules.dotfiles import show_aliases
        show_aliases()

    elif cmd == "/env":
        from nova.modules.dotfiles import show_env
        show_env(args)

    # ─── Persona ───────────────────────────────────────────────
    elif cmd in ("/persona", "/personas"):
        from nova.personas import get_persona_registry
        reg = get_persona_registry()
        if not args or args == "list":
            from rich.table import Table
            table = Table(title="[bold]Personas[/]", border_style="dim cyan",
                          header_style="bold cyan")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="white")
            table.add_column("Description", style="dim")
            table.add_column("Active", style="green", justify="center")
            for p in reg.list_all():
                active = "◆" if reg.active_id == p.id else ""
                table.add_row(p.id, p.name, p.description, active)
            console.print()
            console.print(table)
            console.print()
        else:
            parts = args.split(maxsplit=1)
            sub = parts[0]
            if sub == "use" and len(parts) > 1:
                target = parts[1]
                p = reg.activate(target)
                if p is None:
                    warning(f"Unknown persona: {target}")
                else:
                    # Swap the current brain's persona on the fly
                    brain._persona_id = p.id
                    brain.reset()
                    success(f"Persona activated: {p.name}")
                    if p.greeting:
                        muted(p.greeting)
            elif sub == "show" and len(parts) > 1:
                p = reg.personas.get(parts[1])
                if p is None:
                    warning(f"Unknown persona: {parts[1]}")
                else:
                    from nova.utils.display import summary_panel
                    summary_panel(f"Persona: {p.name}", {
                        "Version": p.version,
                        "Description": p.description,
                        "Tags": ", ".join(p.tags) or "—",
                        "Skills": ", ".join(p.skills) or "—",
                        "Model": p.model or "(default)",
                    })
            else:
                warning("Usage: /persona [list|use <id>|show <id>]")

    # ─── Skills ────────────────────────────────────────────────
    elif cmd in ("/skill", "/skills"):
        from nova.skills import get_registry
        reg = get_registry()
        if not args or args == "list":
            from rich.table import Table
            table = Table(title="[bold]Skills[/]", border_style="dim cyan",
                          header_style="bold cyan")
            table.add_column("ID", style="cyan")
            table.add_column("Version", style="dim")
            table.add_column("Tools", style="magenta")
            table.add_column("Description", style="white")
            table.add_column("On", style="green", justify="center")
            for s in reg.skills.values():
                table.add_row(
                    s.id, s.version, str(len(s.tool_defs)),
                    s.description, "◆" if s.enabled else "",
                )
            console.print()
            console.print(table)
            console.print()
        else:
            parts = args.split(maxsplit=1)
            sub = parts[0]
            if sub == "reload":
                reg.discover()
                success(f"Reloaded {len(reg.skills)} skills")
            elif sub == "show" and len(parts) > 1:
                s = reg.skills.get(parts[1])
                if s is None:
                    warning(f"Unknown skill: {parts[1]}")
                else:
                    info(s.describe())
            elif sub == "enable" and len(parts) > 1:
                if reg.enable(parts[1]):
                    success(f"Enabled {parts[1]}")
                else:
                    warning(f"Unknown skill: {parts[1]}")
            elif sub == "disable" and len(parts) > 1:
                if reg.disable(parts[1]):
                    success(f"Disabled {parts[1]}")
                else:
                    warning(f"Unknown skill: {parts[1]}")
            elif sub == "search" and len(parts) > 1:
                hits = reg.search(parts[1])
                if not hits:
                    info("No matches")
                for s in hits:
                    console.print(f"  [cyan]{s.id}[/] — {s.description}")
            else:
                warning("Usage: /skills [list|reload|show <id>|enable <id>|disable <id>|search <q>]")

    # ─── Memory ────────────────────────────────────────────────
    elif cmd in ("/memory", "/mem"):
        from nova.modules.memory import get_store, memory_summary
        store = get_store()
        if not args or args == "list":
            entries = store.list(limit=20)
            if not entries:
                info("No memories yet. Save some with /mem add <type> <title>::<body>")
            else:
                from rich.table import Table
                table = Table(title="[bold]Memories[/]", border_style="dim cyan",
                              header_style="bold cyan")
                table.add_column("#", style="dim")
                table.add_column("Type", style="magenta")
                table.add_column("Title", style="cyan")
                table.add_column("Body", style="white")
                for e in entries:
                    table.add_row(str(e.id), e.type, e.title, e.body[:60])
                console.print()
                console.print(table)
                muted(memory_summary())
                console.print()
        else:
            parts = args.split(maxsplit=1)
            sub = parts[0]
            rest = parts[1] if len(parts) > 1 else ""
            if sub == "add" and rest:
                bits = rest.split(maxsplit=1)
                type_ = bits[0] if bits[0] in ("user", "feedback", "project", "reference", "fact") else "fact"
                payload = bits[1] if len(bits) > 1 else ""
                title, _, body = payload.partition("::")
                if not title:
                    warning("Usage: /mem add <type> <title>::<body>")
                else:
                    mid = store.add(type_, title.strip(), (body or title).strip())
                    success(f"Saved #{mid}")
            elif sub == "recall" and rest:
                entries = store.search(rest)
                if not entries:
                    info("No matches")
                for e in entries:
                    console.print(f"  [cyan]#{e.id}[/] ({e.type}) [white]{e.title}[/]: [dim]{e.body[:80]}[/]")
            elif sub == "forget" and rest.isdigit():
                if store.delete(int(rest)):
                    success(f"Forgot #{rest}")
                else:
                    warning(f"No memory #{rest}")
            elif sub == "count":
                info(memory_summary())
            else:
                warning("Usage: /mem [list|add <type> <title>::<body>|recall <q>|forget <id>|count]")

    # ─── Hub ───────────────────────────────────────────────────
    elif cmd == "/hub":
        from nova.hub import get_hub
        hub = get_hub()
        parts = args.split(maxsplit=1) if args else ["list"]
        sub = parts[0]
        rest = parts[1] if len(parts) > 1 else ""
        if sub == "refresh":
            result = hub.refresh()
            if result.get("ok"):
                success(f"Hub refreshed ({result['source']}, {result['entries']} entries)")
            else:
                error(result.get("error", "refresh failed"))
        elif sub == "list":
            entries = hub.list()
            if not entries:
                info("Hub index empty — run /hub refresh")
            for e in entries:
                console.print(f"  [cyan]{e.id}[/] v{e.version} — {e.description}")
        elif sub == "search" and rest:
            for e in hub.search(rest):
                console.print(f"  [cyan]{e.id}[/] — {e.description}")
        elif sub == "install" and rest:
            result = hub.install(rest)
            if result.get("ok"):
                success(f"Installed {rest} → {result['installed']}")
                from nova.skills import get_registry
                get_registry().discover()
            else:
                error(result.get("error", "install failed"))
        elif sub == "uninstall" and rest:
            result = hub.uninstall(rest)
            if result.get("ok"):
                success(f"Removed {rest}")
            else:
                error(result.get("error", "uninstall failed"))
        else:
            warning("Usage: /hub [refresh|list|search <q>|install <id>|uninstall <id>]")

    # ─── Gateway ───────────────────────────────────────────────
    elif cmd == "/gateway":
        from nova.gateway import start_gateway, stop_gateway
        parts = args.split() if args else ["status"]
        sub = parts[0]
        if sub == "start":
            gw = start_gateway()
            success(f"Gateway listening on {gw.url}")
            muted(f"Token: ~/.nova/gateway.token")
        elif sub == "stop":
            stop_gateway()
            success("Gateway stopped")
        elif sub == "status":
            from nova.channels import HttpClientChannel
            result = HttpClientChannel().health()
            if result.get("status") == "ok":
                success("Gateway is running")
            else:
                info("Gateway not running (or unreachable)")
        else:
            warning("Usage: /gateway [start|stop|status]")

    # ─── Session ───────────────────────────────────────────────
    elif cmd == "/clear":
        brain.reset()
        success("Conversation cleared")

    elif cmd == "/config":
        from nova.config import load_config
        import yaml
        config = load_config()
        console.print()
        console.print(yaml.dump(config, default_flow_style=False))

    else:
        warning(f"Unknown command: {cmd}. Type /help for available commands.")

    return None


# ─── CLI Commands ───────────────────────────────────────────────────

@main.command()
@click.argument("directory", default=".")
@click.option("--dest", "-d", default=None, help="Destination directory")
@click.option("--dry-run/--execute", default=True, help="Preview changes without moving files")
@click.option("--recursive", "-r", is_flag=True, help="Include subdirectories")
def organize(directory: str, dest: str | None, dry_run: bool, recursive: bool):
    """Organize files in a directory into categorized folders."""
    from nova.modules.organizer import organize_files
    from nova.utils.display import file_table

    mode = "[yellow]DRY RUN[/]" if dry_run else "[green]LIVE[/]"
    info(f"Organizing: {directory} ({mode})")

    actions = organize_files(directory, dest, dry_run=dry_run, recursive=recursive)

    if not actions:
        info("No files to organize.")
        return

    console.print(file_table(actions, title="Organization Plan" if dry_run else "Results"))

    moved = sum(1 for a in actions if "→" in a.get("action", ""))
    skipped = sum(1 for a in actions if "skip" in a.get("action", ""))
    already = sum(1 for a in actions if "already" in a.get("action", ""))

    console.print()
    if dry_run:
        info(f"Would move: {moved} | Skip: {skipped} | Already organized: {already}")
        muted("Run with --execute to apply changes")
    else:
        success(f"Moved: {moved} | Skipped: {skipped} | Already organized: {already}")


@main.command()
@click.argument("directory", default=".")
@click.option("--recursive", "-r", is_flag=True, help="Include subdirectories")
def analyze(directory: str, recursive: bool):
    """Analyze a directory and show file statistics."""
    from nova.modules.organizer import show_analysis
    show_analysis(directory, recursive)


@main.command()
@click.argument("directory", default="~/Downloads")
@click.option("--dest", "-d", default=None, help="Destination for organized files")
@click.option("--dry-run/--live", default=True, help="Preview mode")
def watch(directory: str, dest: str | None, dry_run: bool):
    """Watch a directory and auto-organize new files."""
    from nova.modules.watcher import watch_directory
    watch_directory(directory, destination=dest, dry_run=dry_run)


@main.command()
def system():
    """Show system information."""
    from nova.modules.system import show_system_info, show_disk_usage, show_processes
    show_system_info()
    console.print()
    show_disk_usage()
    console.print()
    show_processes(limit=10)


@main.command()
@click.argument("query", nargs=-1, required=True)
def ask(query: tuple):
    """Ask Nova AI a question (non-interactive)."""
    from nova.modules.ai_brain import AIBrain

    brain = AIBrain()
    question = " ".join(query)
    response = brain.chat(question)
    if response:
        ai_response(response)


@main.command()
@click.argument("directory", default="~")
@click.option("--min-size", "-s", default=100, help="Minimum size in MB")
@click.option("--limit", "-n", default=20, help="Number of results")
def large(directory: str, min_size: int, limit: int):
    """Find large files on your system."""
    from nova.modules.system import find_large_files

    info(f"Searching for files >{min_size}MB in {directory}...")
    files = find_large_files(directory, min_size_mb=min_size, limit=limit)

    if not files:
        info("No large files found.")
        return

    from rich.table import Table
    table = Table(title=f"Large Files (>{min_size}MB)")
    table.add_column("File", style="white")
    table.add_column("Size", style="cyan", justify="right")
    table.add_column("Modified", style="dim")
    table.add_column("Path", style="dim")

    for f in files:
        table.add_row(f["name"], f["size_human"], f["modified"], f["path"])

    console.print(table)


@main.command()
def cleanup():
    """Get cleanup suggestions for your system."""
    from nova.modules.system import cleanup_suggestions

    info("Scanning for cleanup opportunities...")
    suggestions = cleanup_suggestions()

    from rich.table import Table

    console.print()
    info(f"Trash size: [yellow]{suggestions['trash']}[/]")
    info(f"Temp files: [yellow]{suggestions['temp_files']}[/]")

    if suggestions["caches"]:
        console.print()
        table = Table(title="Cache Directories")
        table.add_column("Cache", style="cyan")
        table.add_column("Path", style="dim")
        table.add_column("Size", style="yellow", justify="right")
        for c in suggestions["caches"]:
            table.add_row(c["name"], c["path"], c["size"])
        console.print(table)

    if suggestions["large_files"]:
        console.print()
        table = Table(title="Very Large Files (>500MB)")
        table.add_column("File", style="white")
        table.add_column("Size", style="cyan", justify="right")
        for f in suggestions["large_files"]:
            table.add_row(f["name"], f["size_human"])
        console.print(table)

    console.print()
    muted("Use 'nova organize' to automatically sort files into categories")


@main.command()
def config():
    """Show or edit Nova configuration."""
    from nova.config import load_config, DEFAULT_CONFIG_FILE
    import yaml

    cfg = load_config()
    console.print(f"\n[dim]Config file: {DEFAULT_CONFIG_FILE}[/]\n")
    console.print(yaml.dump(cfg, default_flow_style=False))


@main.command()
def dashboard():
    """Launch the live system dashboard."""
    from nova.modules.dashboard import run_dashboard
    run_dashboard()


@main.command()
@click.argument("directory", default=".")
def code(directory: str):
    """Analyze a codebase for security, debt, and complexity."""
    from nova.modules.code_analyzer import show_codebase_analysis
    show_codebase_analysis(directory)


@main.command()
@click.argument("template", required=False)
@click.argument("name", required=False)
def scaffold(template: str | None, name: str | None):
    """Scaffold a new project from a template."""
    from nova.modules.scaffolder import scaffold_project, list_templates
    if not template:
        list_templates()
    elif not name:
        warning("Usage: nova scaffold <template> <name>")
    else:
        scaffold_project(template, name)


@main.command()
@click.argument("directory", default=".")
def packages(directory: str):
    """List installed packages across managers."""
    from nova.modules.packages import show_packages
    show_packages(directory)


@main.command()
def dev_servers():
    """Find running development servers."""
    from nova.modules.services import show_dev_servers
    show_dev_servers()


@main.command()
def hogs():
    """Show top resource-consuming processes."""
    from nova.modules.services import show_resource_hogs
    show_resource_hogs()


@main.command()
def stats():
    """Show productivity stats and streak."""
    from nova.modules.productivity import show_stats
    show_stats()


# ─── Persona ───────────────────────────────────────────────────────
@main.group()
def persona():
    """Manage Nova personas (SPIRIT.md)."""


@persona.command("list")
def persona_list():
    """List available personas."""
    from nova.personas import get_persona_registry
    from rich.table import Table

    reg = get_persona_registry()
    table = Table(title="Personas", border_style="dim cyan", header_style="bold cyan")
    table.add_column("ID", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Skills", style="magenta")
    for p in reg.list_all():
        table.add_row(p.id, p.description, ", ".join(p.skills) or "—")
    console.print(table)


@persona.command("show")
@click.argument("persona_id")
def persona_show(persona_id: str):
    """Print a persona's full system prompt."""
    from nova.personas import get_persona_registry
    p = get_persona_registry().personas.get(persona_id)
    if p is None:
        error(f"Unknown persona: {persona_id}")
        return
    info(f"{p.name} v{p.version}")
    muted(p.description)
    console.print()
    console.print(p.system_prompt)


@main.command()
def onboard():
    """Run the interactive setup wizard (install-to-textable in 5 minutes)."""
    from nova.onboard import run_onboard
    run_onboard()


# ─── Service (background/autostart) ───────────────────────────────
@main.group()
def service():
    """Manage Nova as a background service (Windows/macOS/Linux)."""


@service.command("install")
def service_install():
    """Install Nova to start on boot/login."""
    from nova.service import install_service
    result = install_service()
    if result.get("ok"):
        success(f"Installed ({result.get('method')})")
    else:
        error(result.get("error", "install failed"))


@service.command("uninstall")
def service_uninstall():
    """Remove the Nova background service."""
    from nova.service import uninstall_service
    result = uninstall_service()
    if result.get("ok"):
        success("Service removed")
    else:
        error(result.get("error", "uninstall failed"))


@service.command("status")
def service_status_cmd():
    """Show current service state."""
    from nova.service import service_status
    result = service_status()
    if not result.get("installed"):
        info("Service not installed")
        return
    info(f"State: {result.get('state', 'unknown')}")


@service.command("start")
def service_start_cmd():
    """Start the Nova service."""
    from nova.service import start_service
    r = start_service()
    success("Started") if r.get("ok") else error(r.get("error", "failed"))


@service.command("stop")
def service_stop_cmd():
    """Stop the Nova service."""
    from nova.service import stop_service
    r = stop_service()
    success("Stopped") if r.get("ok") else error(r.get("error", "failed"))


# ─── Tunnel ───────────────────────────────────────────────────────
@main.group()
def tunnel():
    """Expose the local gateway publicly via Cloudflare Tunnel."""


@tunnel.command("start")
@click.option("--port", default=7878, show_default=True, type=int)
def tunnel_start(port: int):
    """Start a quick tunnel to the local gateway."""
    from nova.tunnel import CloudflareTunnel
    t = CloudflareTunnel()
    if not t.is_installed():
        info("Installing cloudflared...")
        r = t.install()
        if not r.get("ok"):
            error(r.get("error", "install failed"))
            return
    info("Starting tunnel — this can take ~10s...")
    r = t.start(local_port=port)
    if r.get("ok"):
        success(f"Public URL: {r['url']}")
        muted(f"PID: {r.get('pid')}")
    else:
        error(r.get("error", "tunnel failed"))


@tunnel.command("stop")
def tunnel_stop():
    """Stop the running tunnel."""
    from nova.tunnel import CloudflareTunnel
    CloudflareTunnel().stop()
    success("Tunnel stopped")


@tunnel.command("status")
def tunnel_status():
    """Show tunnel state and public URL."""
    from nova.tunnel import CloudflareTunnel
    s = CloudflareTunnel().status()
    if s.get("running"):
        info(f"Running — {s.get('url')} (PID {s.get('pid')})")
    else:
        info("Not running")


@tunnel.command("install")
def tunnel_install():
    """Download the cloudflared binary into ~/.nova/bin/."""
    from nova.tunnel import CloudflareTunnel
    r = CloudflareTunnel().install()
    if r.get("ok"):
        success(f"Installed: {r['path']}")
    else:
        error(r.get("error", "install failed"))


@main.command("ask-as")
@click.argument("persona_id")
@click.argument("query", nargs=-1, required=True)
def ask_as(persona_id: str, query: tuple):
    """Ask Nova AI a question using a specific persona (non-interactive)."""
    from nova.modules.ai_brain import AIBrain
    brain = AIBrain(persona_id=persona_id)
    response = brain.chat(" ".join(query))
    if response:
        ai_response(response)


# ─── Skills ────────────────────────────────────────────────────────
@main.group()
def skills():
    """Manage Nova skills."""


@skills.command("list")
def skills_list():
    """List loaded skills."""
    from nova.skills import get_registry
    from rich.table import Table
    reg = get_registry()
    table = Table(title="Skills", border_style="dim cyan", header_style="bold cyan")
    table.add_column("ID", style="cyan")
    table.add_column("Version", style="dim")
    table.add_column("Tools", style="magenta")
    table.add_column("Description", style="white")
    for s in reg.skills.values():
        table.add_row(s.id, s.version, str(len(s.tool_defs)), s.description)
    console.print(table)


@skills.command("reload")
def skills_reload():
    """Re-scan skill directories."""
    from nova.skills import get_registry
    reg = get_registry()
    reg.discover()
    success(f"Reloaded {len(reg.skills)} skills")


# ─── Memory ────────────────────────────────────────────────────────
@main.group()
def memory():
    """Manage persistent memory."""


@memory.command("list")
@click.option("--type", "type_", default=None, help="Filter by type")
def memory_list(type_: str | None):
    """List stored memories."""
    from nova.modules.memory import get_store
    from rich.table import Table
    entries = get_store().list(type_=type_, limit=50)
    if not entries:
        info("No memories stored.")
        return
    table = Table(title="Memories", border_style="dim cyan", header_style="bold cyan")
    table.add_column("#", style="dim")
    table.add_column("Type", style="magenta")
    table.add_column("Title", style="cyan")
    table.add_column("Body", style="white")
    for e in entries:
        table.add_row(str(e.id), e.type, e.title, e.body[:80])
    console.print(table)


@memory.command("add")
@click.argument("type_", type=click.Choice(["user", "feedback", "project", "reference", "fact"]))
@click.argument("title")
@click.argument("body")
def memory_add(type_: str, title: str, body: str):
    """Save a new memory."""
    from nova.modules.memory import remember
    mid = remember(type_, title, body)
    success(f"Saved memory #{mid}")


@memory.command("recall")
@click.argument("query", nargs=-1, required=True)
def memory_recall(query: tuple):
    """Search memory by keyword."""
    from nova.modules.memory import recall
    results = recall(" ".join(query))
    if not results:
        info("No matches")
        return
    for r in results:
        console.print(f"  [cyan]#{r['id']}[/] ({r['type']}) [white]{r['title']}[/]: [dim]{r['body'][:100]}[/]")


# ─── Hub ───────────────────────────────────────────────────────────
@main.group()
def hub():
    """Nova Hub — browse and install skills."""


@hub.command("refresh")
def hub_refresh():
    """Refresh the hub index."""
    from nova.hub import get_hub
    result = get_hub().refresh()
    if result.get("ok"):
        success(f"Hub refreshed ({result['source']}, {result['entries']} entries)")
    else:
        error(result.get("error", "refresh failed"))


@hub.command("list")
def hub_list():
    """List hub entries."""
    from nova.hub import get_hub
    for e in get_hub().list():
        console.print(f"  [cyan]{e.id}[/] v{e.version} — {e.description}")


@hub.command("install")
@click.argument("entry_id")
def hub_install(entry_id: str):
    """Install a skill from the hub."""
    from nova.hub import get_hub
    result = get_hub().install(entry_id)
    if result.get("ok"):
        success(f"Installed {entry_id}")
    else:
        error(result.get("error", "install failed"))


# ─── Gateway ───────────────────────────────────────────────────────
@main.group()
def gateway():
    """Manage the Nova gateway HTTP server."""


@gateway.command("start")
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", default=7878, show_default=True, type=int)
@click.option("--foreground/--background", default=True)
def gateway_start(host: str, port: int, foreground: bool):
    """Start the Nova gateway."""
    from nova.gateway import start_gateway
    gw = start_gateway(host=host, port=port)
    success(f"Gateway listening on {gw.url}")
    muted(f"Token file: ~/.nova/gateway.token")
    if foreground:
        info("Running in foreground — Ctrl+C to stop")
        try:
            import time
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            from nova.gateway import stop_gateway
            stop_gateway()
            success("Gateway stopped")


@gateway.command("status")
def gateway_status():
    """Check gateway health."""
    from nova.channels import HttpClientChannel
    result = HttpClientChannel().health()
    if result.get("status") == "ok":
        success("Gateway is running")
    else:
        info(f"Gateway not reachable: {result.get('error', 'unknown')}")


# ─── Channels ──────────────────────────────────────────────────────
@main.group()
def channel():
    """Run a Nova channel adapter."""


@channel.command("telegram")
@click.option("--persona", default=None, help="Persona to use for replies")
def channel_telegram(persona: str | None):
    """Run the Telegram long-poll channel. Requires TELEGRAM_BOT_TOKEN."""
    from nova.channels import TelegramChannel
    ch = TelegramChannel(persona=persona)
    info("Telegram channel starting — Ctrl+C to stop")
    try:
        ch.run()
    except RuntimeError as e:
        error(str(e))


if __name__ == "__main__":
    main()
