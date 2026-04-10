"""Rich terminal display engine v2 — gradients, dashboard layouts, status bar, and beautiful panels."""

import time
import platform
from datetime import datetime
from rich.console import Console, Group
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
from rich.layout import Layout
from rich.align import Align
from rich import box

nova_theme = Theme({
    "info": "cyan",
    "success": "green",
    "warning": "yellow",
    "error": "red bold",
    "highlight": "magenta",
    "muted": "dim",
    "nova": "bold cyan",
    "accent": "bold magenta",
    "grad1": "bold #00d4ff",
    "grad2": "bold #7b68ee",
    "grad3": "bold #ff6ec7",
    "bar.back": "grey23",
    "bar.complete": "#00d4ff",
    "bar.finished": "#00ff88",
})

console = Console(theme=nova_theme)

# ─── Gradient Helpers ────────────────────────────────────────────

GRADIENT_CYAN_PURPLE = ["#00d4ff", "#1ea8ff", "#3d7cff", "#5b50ff", "#7b68ee"]
GRADIENT_CYAN_GREEN = ["#00d4ff", "#00dfb8", "#00ea90", "#00f468", "#00ff44"]
GRADIENT_FIRE = ["#ff6ec7", "#ff5e5e", "#ff8c42", "#ffbb33", "#ffe135"]


def gradient_text(text: str, colors: list[str] | None = None) -> Text:
    """Create text with gradient coloring."""
    colors = colors or GRADIENT_CYAN_PURPLE
    rich_text = Text()
    step = max(1, len(text) // len(colors))
    for i, char in enumerate(text):
        color_idx = min(i // step, len(colors) - 1)
        rich_text.append(char, style=colors[color_idx])
    return rich_text


# ─── Banner & Welcome ───────────────────────────────────────────

def banner():
    """Display the Nova Agent banner with gradient animation."""
    logo_lines = [
        "  ███╗   ██╗ ██████╗ ██╗   ██╗ █████╗ ",
        "  ████╗  ██║██╔═══██╗██║   ██║██╔══██╗",
        "  ██╔██╗ ██║██║   ██║██║   ██║███████║",
        "  ██║╚██╗██║██║   ██║╚██╗ ██╔╝██╔══██║",
        "  ██║ ╚████║╚██████╔╝ ╚████╔╝ ██║  ██║",
        "  ╚═╝  ╚═══╝ ╚═════╝   ╚═══╝  ╚═╝  ╚═╝",
    ]

    gradients = [
        ["#00d4ff", "#00d4ff", "#1ea8ff", "#3d7cff", "#5b50ff", "#7b68ee"],
        ["#1ea8ff", "#1ea8ff", "#3d7cff", "#5b50ff", "#7b68ee", "#9966cc"],
        ["#3d7cff", "#3d7cff", "#5b50ff", "#7b68ee", "#9966cc", "#bb55aa"],
        ["#5b50ff", "#5b50ff", "#7b68ee", "#9966cc", "#bb55aa", "#dd4488"],
        ["#7b68ee", "#7b68ee", "#9966cc", "#bb55aa", "#dd4488", "#ff3366"],
        ["#9966cc", "#9966cc", "#bb55aa", "#dd4488", "#ff3366", "#ff6ec7"],
    ]

    content = Text()
    with Live(console=console, refresh_per_second=30, transient=True) as live:
        built = Text()
        for idx, line in enumerate(logo_lines):
            grad = gradients[idx]
            step = max(1, len(line) // len(grad))
            for i, ch in enumerate(line):
                ci = min(i // step, len(grad) - 1)
                built.append(ch, style=f"bold {grad[ci]}")
            built.append("\n")
            live.update(Panel(
                Align.center(built + Text("\n  AI-Powered Computer Agent", style="dim")),
                border_style="#5b50ff",
                box=box.DOUBLE_EDGE,
                padding=(0, 1),
            ))
            time.sleep(0.08)
        content = built

    # Final static banner
    subtitle_parts = Text()
    subtitle_parts.append("  Powered by ", style="dim")
    subtitle_parts.append("Anthropic Claude", style="bold #00d4ff")
    subtitle_parts.append("  │  ", style="dim")
    subtitle_parts.append(f"v0.2.0", style="dim #7b68ee")
    subtitle_parts.append("  │  ", style="dim")
    subtitle_parts.append(platform.node(), style="dim #ff6ec7")

    console.print(Panel(
        Align.center(Group(
            content,
            Text(),
            Align.center(subtitle_parts),
        )),
        border_style="#5b50ff",
        box=box.DOUBLE_EDGE,
        padding=(0, 1),
    ))


def welcome_dashboard():
    """Show a quick dashboard on startup."""
    import psutil

    now = datetime.now()
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    cpu = psutil.cpu_percent(interval=0.3)

    # Time and greeting
    hour = now.hour
    greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"

    # Build mini status cards
    cpu_color = "#00ff88" if cpu < 50 else "#ffbb33" if cpu < 80 else "#ff5e5e"
    mem_color = "#00ff88" if mem.percent < 60 else "#ffbb33" if mem.percent < 85 else "#ff5e5e"
    disk_color = "#00ff88" if disk.percent < 75 else "#ffbb33" if disk.percent < 90 else "#ff5e5e"

    cpu_bar = _mini_bar(cpu / 100, cpu_color)
    mem_bar = _mini_bar(mem.percent / 100, mem_color)
    disk_bar = _mini_bar(disk.percent / 100, disk_color)

    status = Table.grid(padding=(0, 2))
    status.add_column(justify="center", min_width=22)
    status.add_column(justify="center", min_width=22)
    status.add_column(justify="center", min_width=22)

    status.add_row(
        Panel(f"[bold {cpu_color}]CPU {cpu:.0f}%[/]\n{cpu_bar}",
              border_style="dim", box=box.ROUNDED, width=22, title="[dim]processor[/]"),
        Panel(f"[bold {mem_color}]RAM {mem.percent:.0f}%[/]\n{mem_bar}",
              border_style="dim", box=box.ROUNDED, width=22, title="[dim]memory[/]"),
        Panel(f"[bold {disk_color}]Disk {disk.percent:.0f}%[/]\n{disk_bar}",
              border_style="dim", box=box.ROUNDED, width=22, title="[dim]storage[/]"),
    )

    console.print()
    console.print(Align.center(Text(f"{greeting}! Today is {now.strftime('%A, %B %d')}", style="dim")))
    console.print()
    console.print(Align.center(status))
    console.print()
    console.print(Align.center(Text("Type /help for commands or just ask me anything", style="dim italic")))
    console.print()


def _mini_bar(fraction: float, color: str, width: int = 16) -> str:
    """Create a mini progress bar string."""
    filled = int(fraction * width)
    empty = width - filled
    return f"[{color}]{'━' * filled}[/][dim]{'━' * empty}[/]"


# ─── Section Headers ────────────────────────────────────────────

def section_header(title: str, style: str = "cyan", icon: str = ""):
    """Display a styled section header with optional icon."""
    console.print()
    prefix = f"{icon} " if icon else ""
    console.print(Rule(
        f"[bold {style}]{prefix}{title}[/]",
        style=style,
        characters="─",
    ))
    console.print()


# ─── Status Messages ────────────────────────────────────────────

def success(msg: str):
    console.print(f"  [bold green]✓[/] {msg}")

def error(msg: str):
    console.print(f"  [bold red]✗[/] {msg}")

def warning(msg: str):
    console.print(f"  [bold yellow]⚠[/] {msg}")

def info(msg: str):
    console.print(f"  [bold cyan]→[/] {msg}")

def muted(msg: str):
    console.print(f"  [dim]{msg}[/]")

def step(number: int, total: int, msg: str):
    """Display a numbered step with gradient progress."""
    pct = number / total
    bar = _mini_bar(pct, "#7b68ee", 10)
    console.print(f"  {bar} [bold]({number}/{total})[/] {msg}")


# ─── AI Display ─────────────────────────────────────────────────

def ai_thinking():
    """Display an AI thinking animation with style."""
    return Progress(
        SpinnerColumn("dots12", style="#7b68ee"),
        TextColumn("[#7b68ee]Nova is thinking...[/]"),
        TimeElapsedColumn(),
        transient=True,
        console=console,
    )


def ai_response(text: str):
    """Display AI response in a beautifully styled panel."""
    console.print()
    md = Markdown(text)

    # Gradient title
    title = Text()
    title.append("◆ ", style="bold #7b68ee")
    title.append("Nova", style="bold #00d4ff")

    console.print(Panel(
        md,
        border_style="#5b50ff",
        box=box.ROUNDED,
        title=title,
        title_align="left",
        subtitle="[dim #7b68ee]powered by claude[/]",
        subtitle_align="right",
        padding=(1, 2),
    ))
    console.print()


# ─── Progress Bars ──────────────────────────────────────────────

def task_progress(description: str = "Processing", total: int = 100):
    """Create a beautiful animated progress bar."""
    return Progress(
        SpinnerColumn("dots12", style="#7b68ee"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40, style="grey23", complete_style="#00d4ff", finished_style="#00ff88"),
        TaskProgressColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
    )


def scan_progress(description: str = "Scanning"):
    """Create a scanning animation."""
    return Progress(
        SpinnerColumn("dots12", style="#ff6ec7"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=30, style="grey23", complete_style="#ff6ec7", finished_style="#00ff88"),
        MofNCompleteColumn(),
        TextColumn("[dim]files[/]"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    )


def multi_step_progress(steps: list[str]):
    """Create a multi-step progress display."""
    with Live(console=console, refresh_per_second=12) as live:
        for i, step_name in enumerate(steps):
            completed = [f"  [green]✓[/] [dim]{s}[/]" for s in steps[:i]]
            current = f"  [bold #7b68ee]▸[/] [bold]{step_name}...[/]"
            pending = [f"  [dim]○ {s}[/]" for s in steps[i + 1:]]
            all_lines = "\n".join(completed + [current] + pending)

            pct = (i + 1) / len(steps)
            bar = _mini_bar(pct, "#7b68ee", 30)

            live.update(Panel(
                f"{all_lines}\n\n  {bar}  [dim]{i + 1}/{len(steps)}[/]",
                title="[bold #7b68ee]Progress[/]",
                title_align="left",
                border_style="#5b50ff",
                box=box.ROUNDED,
                padding=(1, 2),
            ))
            yield step_name  # Caller does the work for this step


# ─── Tables & Panels ───────────────────────────────────────────

def nova_table(title: str = "", columns: list[tuple] | None = None) -> Table:
    """Create a consistently styled Nova table."""
    table = Table(
        title=f"[bold]{title}[/]" if title else None,
        show_lines=False,
        border_style="dim #5b50ff",
        header_style="bold #00d4ff",
        row_styles=["", "dim"],
        box=box.SIMPLE_HEAD,
        padding=(0, 1),
    )
    if columns:
        for col_name, col_style, col_kwargs in columns:
            table.add_column(col_name, style=col_style, **col_kwargs)
    return table


def file_tree(root_path: str, files: list[dict]) -> Tree:
    """Create a visual file tree with icons."""
    tree = Tree(f"[bold #00d4ff]{root_path}[/]", guide_style="dim #5b50ff")
    folders = {}
    for f in files:
        category = f.get("category", "Other")
        if category not in folders:
            folders[category] = tree.add(f"[bold green]{_category_icon(category)} {category}[/]")
        icon = _file_icon(f.get("extension", ""))
        folders[category].add(f"{icon} {f['name']} [dim]({f.get('size_human', '')})[/]")
    return tree


def file_table(files: list[dict], title: str = "Files") -> Table:
    """Create a formatted file table."""
    table = nova_table(title, [
        ("#", "dim", {"justify": "right", "width": 4}),
        ("File", "white", {}),
        ("Size", "#00d4ff", {"justify": "right"}),
        ("Category", "green", {}),
        ("Action", "yellow", {}),
    ])
    for i, f in enumerate(files, 1):
        table.add_row(str(i), f["name"], f.get("size_human", ""), f.get("category", ""), f.get("action", ""))
    return table


def stats_table(stats: dict, title: str = "Statistics") -> Table:
    """Create a stats table with visual styling."""
    table = nova_table(title, [
        ("Metric", "#00d4ff", {}),
        ("Value", "white bold", {"justify": "right"}),
    ])
    for key, value in stats.items():
        table.add_row(key, str(value))
    return table


def summary_panel(title: str, items: dict, style: str = "#00d4ff"):
    """Display a summary panel with key-value pairs."""
    lines = []
    for k, v in items.items():
        lines.append(f"  [{style}]{k}:[/]  {v}")
    console.print(Panel(
        "\n".join(lines),
        title=f"[bold {style}]{title}[/]",
        title_align="left",
        border_style=style,
        box=box.ROUNDED,
        padding=(1, 1),
    ))


def metric_cards(cards: list[dict]):
    """Display a row of metric cards.

    Each card: {"label": str, "value": str, "color": str, "icon": str}
    """
    panels = []
    for card in cards:
        color = card.get("color", "#00d4ff")
        icon = card.get("icon", "●")
        panels.append(Panel(
            Align.center(Text.from_markup(
                f"[bold {color}]{card['value']}[/]\n[dim]{icon} {card['label']}[/]"
            )),
            border_style="dim",
            box=box.ROUNDED,
            width=20,
        ))

    console.print(Columns(panels, align="center", padding=(0, 1)))


def completion_animation(msg: str = "Done!"):
    """Display a task completion animation."""
    frames = ["◐", "◓", "◑", "◒", "●"]
    with Live(console=console, refresh_per_second=15, transient=True) as live:
        for frame in frames:
            live.update(Text(f"  {frame} {msg}", style="bold green"))
            time.sleep(0.1)
    success(msg)


# ─── Icons ──────────────────────────────────────────────────────

def _category_icon(category: str) -> str:
    icons = {
        "Documents": "📄", "Images": "🖼", "Videos": "🎬",
        "Audio": "🎵", "Archives": "📦", "Code": "💻",
        "Data": "📊", "Installers": "💿", "Fonts": "🔤",
        "Design": "🎨", "Other": "📎",
    }
    return icons.get(category, "📁")


def _file_icon(ext: str) -> str:
    icons = {
        ".py": "🐍", ".js": "📜", ".ts": "📘", ".go": "🔵", ".rs": "🦀",
        ".java": "☕", ".rb": "💎", ".pdf": "📄", ".doc": "📝", ".docx": "📝",
        ".jpg": "🖼", ".png": "🖼", ".gif": "🎞", ".svg": "🎨",
        ".mp4": "🎬", ".mkv": "🎬", ".mp3": "🎵", ".wav": "🎵",
        ".zip": "📦", ".tar": "📦", ".gz": "📦",
        ".csv": "📊", ".json": "📋", ".yaml": "⚙️",
        ".exe": "💿", ".dmg": "💿", ".deb": "💿",
    }
    return icons.get(ext.lower(), "📎")
