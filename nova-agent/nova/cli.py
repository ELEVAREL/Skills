"""Nova Agent CLI — main entry point."""

import sys
import click
from pathlib import Path

from nova.utils.display import (
    console, banner, success, error, warning, info, muted, ai_response,
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

    banner()
    console.print("[dim]Type a command or ask me anything. Type /help for commands, /quit to exit.[/]")
    console.print()

    ensure_config_dir()
    history_file = DEFAULT_CONFIG_DIR / "history"

    style = Style.from_dict({
        "prompt": "cyan bold",
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
                [("class:prompt", "nova > ")],
            ).strip()

            if not user_input:
                continue

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
            "File Management": {
                "/organize <dir>": "Organize files into categorized folders",
                "/analyze <dir>": "Analyze directory contents and statistics",
                "/watch <dir>": "Auto-organize new files as they arrive",
                "/large [dir]": "Find large files (>50MB)",
                "/duplicates [dir]": "Find duplicate files by content hash",
                "/recent [dir]": "Show recently modified files",
            },
            "Search": {
                "/find <name>": "Search for files by name",
                "/grep <pattern>": "Search file contents",
                "/recent [dir]": "Recently modified files",
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


if __name__ == "__main__":
    main()
