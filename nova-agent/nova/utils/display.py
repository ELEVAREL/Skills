"""Rich terminal display utilities for Nova Agent with animations."""

import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.progress import (
    Progress, SpinnerColumn, TextColumn, BarColumn,
    TimeElapsedColumn, TaskProgressColumn, MofNCompleteColumn,
)
from rich.live import Live
from rich.markdown import Markdown
from rich.theme import Theme
from rich.columns import Columns
from rich.text import Text
from rich.rule import Rule

nova_theme = Theme({
    "info": "cyan",
    "success": "green",
    "warning": "yellow",
    "error": "red bold",
    "highlight": "magenta",
    "muted": "dim",
    "nova": "bold cyan",
    "accent": "bold magenta",
})

console = Console(theme=nova_theme)


def banner():
    """Display the Nova Agent banner with animation."""
    lines = [
        "[bold cyan]  ╔╗╔╔═╗╦  ╦╔═╗[/]",
        "[bold cyan]  ║║║║ ║╚╗╔╝╠═╣[/]",
        "[bold cyan]  ╝╚╝╚═╝ ╚╝ ╩ ╩[/]",
    ]

    # Animate the banner line by line
    content = ""
    with Live(console=console, refresh_per_second=20) as live:
        for line in lines:
            content += line + "\n"
            live.update(Panel.fit(
                content + "[dim]  AI-Powered Computer Agent[/]\n"
                "[dim]  Powered by Anthropic Claude[/]",
                border_style="cyan",
                padding=(0, 2),
            ))
            time.sleep(0.12)

        # Final render with subtitle
        live.update(Panel.fit(
            content + "[dim]  AI-Powered Computer Agent[/]\n"
            "[dim]  Powered by Anthropic Claude[/]",
            border_style="cyan",
            padding=(0, 2),
            subtitle="[dim]v0.1.0[/]",
        ))


def section_header(title: str, style: str = "cyan"):
    """Display an animated section header."""
    console.print()
    console.print(Rule(f"[bold {style}] {title} [/]", style=style))
    console.print()


def success(msg: str):
    console.print(f"  [success]✓[/] {msg}")


def error(msg: str):
    console.print(f"  [error]✗[/] {msg}")


def warning(msg: str):
    console.print(f"  [warning]⚠[/] {msg}")


def info(msg: str):
    console.print(f"  [info]→[/] {msg}")


def muted(msg: str):
    console.print(f"  [muted]{msg}[/]")


def step(number: int, total: int, msg: str):
    """Display a numbered step indicator."""
    console.print(f"  [cyan]({number}/{total})[/] {msg}")


def ai_thinking():
    """Display an AI thinking animation. Returns a context manager."""
    return Progress(
        SpinnerColumn("dots", style="cyan"),
        TextColumn("[cyan]Nova is thinking...[/]"),
        TimeElapsedColumn(),
        transient=True,
        console=console,
    )


def ai_response(text: str):
    """Display AI response with markdown rendering in a panel."""
    console.print()
    md = Markdown(text)
    console.print(Panel(
        md,
        border_style="cyan",
        title="[bold cyan]Nova[/]",
        title_align="left",
        padding=(1, 2),
    ))
    console.print()


def task_progress(description: str = "Processing", total: int = 100):
    """Create an animated task progress bar."""
    return Progress(
        SpinnerColumn("dots", style="cyan"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40, style="dim", complete_style="cyan", finished_style="green"),
        TaskProgressColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
    )


def scan_progress(description: str = "Scanning"):
    """Create a scanning animation progress bar."""
    return Progress(
        SpinnerColumn("dots12", style="cyan"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=30, style="dim", complete_style="magenta", finished_style="green"),
        MofNCompleteColumn(),
        TextColumn("[dim]files[/]"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    )


def file_tree(root_path: str, files: list[dict]) -> Tree:
    """Create a visual file tree with icons."""
    tree = Tree(f"[bold cyan]{root_path}[/]", guide_style="dim cyan")
    folders = {}
    for f in files:
        category = f.get("category", "Other")
        if category not in folders:
            folders[category] = tree.add(f"[bold green]{_category_icon(category)} {category}[/]")
        icon = _file_icon(f.get("extension", ""))
        folders[category].add(f"{icon} {f['name']} [muted]({f.get('size_human', '')})[/]")
    return tree


def file_table(files: list[dict], title: str = "Files") -> Table:
    """Create a formatted file table with borders."""
    table = Table(
        title=f"[bold]{title}[/]",
        show_lines=False,
        border_style="dim cyan",
        header_style="bold cyan",
        row_styles=["", "dim"],
    )
    table.add_column("#", style="dim", justify="right", width=4)
    table.add_column("File", style="white")
    table.add_column("Size", style="cyan", justify="right")
    table.add_column("Category", style="green")
    table.add_column("Action", style="yellow")
    for i, f in enumerate(files, 1):
        table.add_row(str(i), f["name"], f.get("size_human", ""), f.get("category", ""), f.get("action", ""))
    return table


def stats_table(stats: dict, title: str = "Statistics") -> Table:
    """Create a stats table with visual styling."""
    table = Table(
        title=f"[bold]{title}[/]",
        show_lines=False,
        border_style="dim cyan",
        header_style="bold cyan",
    )
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white bold", justify="right")
    for key, value in stats.items():
        table.add_row(key, str(value))
    return table


def summary_panel(title: str, items: dict, style: str = "cyan"):
    """Display a summary panel with key-value pairs."""
    lines = "\n".join(f"[{style}]{k}:[/] {v}" for k, v in items.items())
    console.print(Panel(
        lines,
        title=f"[bold {style}]{title}[/]",
        title_align="left",
        border_style=style,
        padding=(1, 2),
    ))


def completion_animation(msg: str = "Done!"):
    """Display a task completion animation."""
    with Progress(
        SpinnerColumn("dots", style="green"),
        TextColumn(f"[green]{msg}[/]"),
        transient=True,
        console=console,
    ) as progress:
        task = progress.add_task("", total=1)
        time.sleep(0.5)
        progress.update(task, completed=1)
    success(msg)


def _category_icon(category: str) -> str:
    """Get icon for a file category."""
    icons = {
        "Documents": "📄", "Images": "🖼️", "Videos": "🎬",
        "Audio": "🎵", "Archives": "📦", "Code": "💻",
        "Data": "📊", "Installers": "💿", "Fonts": "🔤",
        "Design": "🎨", "Other": "📎",
    }
    return icons.get(category, "📁")


def _file_icon(ext: str) -> str:
    """Get an icon for a file extension."""
    icons = {
        ".py": "🐍", ".js": "📜", ".ts": "📘", ".go": "🔵", ".rs": "🦀",
        ".java": "☕", ".rb": "💎", ".pdf": "📄", ".doc": "📝", ".docx": "📝",
        ".jpg": "🖼️", ".png": "🖼️", ".gif": "🎞️", ".svg": "🎨",
        ".mp4": "🎬", ".mkv": "🎬", ".mp3": "🎵", ".wav": "🎵",
        ".zip": "📦", ".tar": "📦", ".gz": "📦",
        ".csv": "📊", ".json": "📋", ".yaml": "⚙️",
        ".exe": "💿", ".dmg": "💿", ".deb": "💿",
    }
    return icons.get(ext.lower(), "📎")
