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
        console.print()
        help_text = {
            "/organize <dir>": "Organize files in a directory",
            "/analyze <dir>": "Analyze a directory's contents",
            "/watch <dir>": "Auto-organize new files as they arrive",
            "/system": "Show system information",
            "/processes": "Show top processes",
            "/disks": "Show disk usage",
            "/large [dir]": "Find large files",
            "/cleanup": "Get cleanup suggestions",
            "/clear": "Clear conversation history",
            "/config": "Show current configuration",
            "/help": "Show this help",
            "/quit": "Exit Nova",
        }
        from rich.table import Table
        table = Table(title="Nova Commands", show_lines=False)
        table.add_column("Command", style="cyan")
        table.add_column("Description", style="white")
        for c, desc in help_text.items():
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
