"""Live dashboard module — real-time system monitoring like htop."""

import time
from datetime import datetime

import psutil

from nova.utils.display import (
    console, _mini_bar, nova_table, metric_cards,
)
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.text import Text
from rich.align import Align
from rich import box


def _build_dashboard() -> Panel:
    """Build a single dashboard frame."""
    now = datetime.now().strftime("%H:%M:%S")
    cpu = psutil.cpu_percent(interval=0)
    cpu_per_core = psutil.cpu_percent(percpu=True)
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    disk = psutil.disk_usage("/")
    net = psutil.net_io_counters()
    temps = {}
    try:
        temps = psutil.sensors_temperatures()
    except (AttributeError, FileNotFoundError):
        pass

    # ── CPU Section ──
    cpu_color = "#00ff88" if cpu < 50 else "#ffbb33" if cpu < 80 else "#ff5e5e"
    cpu_section = Text()
    cpu_section.append(f"  CPU Usage: ", style="dim")
    cpu_section.append(f"{cpu:.1f}%\n", style=f"bold {cpu_color}")

    # Per-core bars
    cores_per_row = min(8, len(cpu_per_core))
    for i, core_pct in enumerate(cpu_per_core):
        c = "#00ff88" if core_pct < 50 else "#ffbb33" if core_pct < 80 else "#ff5e5e"
        bar = _mini_bar(core_pct / 100, c, 8)
        cpu_section.append(f"  C{i:<2d}")
        cpu_section.append_text(Text.from_markup(f"{bar} {core_pct:5.1f}%\n"))
        if (i + 1) % cores_per_row == 0 and i + 1 < len(cpu_per_core):
            pass  # Just continue on next line

    cpu_panel = Panel(cpu_section, title="[bold #00d4ff]CPU[/]", border_style="dim #5b50ff",
                      box=box.ROUNDED)

    # ── Memory Section ──
    mem_color = "#00ff88" if mem.percent < 60 else "#ffbb33" if mem.percent < 85 else "#ff5e5e"
    mem_text = Text()
    mem_text.append(f"  RAM:  ", style="dim")
    mem_text.append_text(Text.from_markup(
        f"{_mini_bar(mem.percent / 100, mem_color, 20)} "
        f"[bold {mem_color}]{mem.percent:.0f}%[/] "
        f"[dim]({_h(mem.used)} / {_h(mem.total)})[/]\n"
    ))
    if swap.total > 0:
        sw_color = "#00ff88" if swap.percent < 50 else "#ffbb33"
        mem_text.append(f"  Swap: ", style="dim")
        mem_text.append_text(Text.from_markup(
            f"{_mini_bar(swap.percent / 100, sw_color, 20)} "
            f"[bold {sw_color}]{swap.percent:.0f}%[/] "
            f"[dim]({_h(swap.used)} / {_h(swap.total)})[/]\n"
        ))

    mem_panel = Panel(mem_text, title="[bold #7b68ee]Memory[/]", border_style="dim #5b50ff",
                      box=box.ROUNDED)

    # ── Top Processes ──
    procs = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            pi = p.info
            procs.append(pi)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    procs.sort(key=lambda x: (x.get("cpu_percent") or 0), reverse=True)

    proc_table = Table(show_header=True, header_style="bold #00d4ff", box=None,
                       padding=(0, 1), show_edge=False)
    proc_table.add_column("PID", style="dim", width=7, justify="right")
    proc_table.add_column("Process", style="white", min_width=20)
    proc_table.add_column("CPU%", style="#ffbb33", width=7, justify="right")
    proc_table.add_column("MEM%", style="#7b68ee", width=7, justify="right")

    for p in procs[:12]:
        proc_table.add_row(
            str(p.get("pid", "")),
            (p.get("name") or "?")[:25],
            f"{p.get('cpu_percent', 0):.1f}",
            f"{p.get('memory_percent', 0):.1f}",
        )

    proc_panel = Panel(proc_table, title="[bold #ff6ec7]Processes[/]",
                       border_style="dim #5b50ff", box=box.ROUNDED)

    # ── Network & Disk ──
    net_text = Text()
    net_text.append(f"  ↓ Received: {_h(net.bytes_recv)}\n", style="#00d4ff")
    net_text.append(f"  ↑ Sent:     {_h(net.bytes_sent)}\n", style="#ff6ec7")
    net_text.append(f"  Packets:    {net.packets_recv + net.packets_sent:,}\n", style="dim")

    disk_color = "#00ff88" if disk.percent < 75 else "#ffbb33" if disk.percent < 90 else "#ff5e5e"
    net_text.append(f"\n  Disk: ", style="dim")
    net_text.append_text(Text.from_markup(
        f"{_mini_bar(disk.percent / 100, disk_color, 14)} [{disk_color}]{disk.percent}%[/]"
    ))
    net_text.append(f"\n  Free: {_h(disk.free)}\n", style="dim")

    side_panel = Panel(net_text, title="[bold #00d4ff]Network & Disk[/]",
                       border_style="dim #5b50ff", box=box.ROUNDED)

    # ── Layout ──
    layout = Layout()
    layout.split_column(
        Layout(name="top", size=3),
        Layout(name="middle"),
        Layout(name="bottom"),
    )
    layout["top"].update(Align.center(Text.from_markup(
        f"[bold #00d4ff]◆ Nova Dashboard[/]  [dim]│[/]  "
        f"[dim]{now}[/]  [dim]│[/]  "
        f"[dim]Press [bold]Ctrl+C[/bold] to exit[/]"
    )))
    layout["middle"].split_row(
        Layout(cpu_panel, ratio=1),
        Layout(mem_panel, ratio=1),
    )
    layout["bottom"].split_row(
        Layout(proc_panel, ratio=2),
        Layout(side_panel, ratio=1),
    )

    return Panel(layout, border_style="#5b50ff", box=box.DOUBLE_EDGE, padding=0)


def run_dashboard(refresh_rate: float = 1.0):
    """Run the live dashboard."""
    # Prime CPU readings
    psutil.cpu_percent(percpu=True)

    try:
        with Live(console=console, refresh_per_second=int(1 / refresh_rate), screen=True) as live:
            while True:
                live.update(_build_dashboard())
                time.sleep(refresh_rate)
    except KeyboardInterrupt:
        pass


def _h(b: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if b < 1024:
            return f"{b:.1f}{unit}"
        b /= 1024
    return f"{b:.1f}PB"
