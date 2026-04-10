"""System information and management module."""

import os
import platform
import subprocess
from pathlib import Path
from datetime import datetime

import psutil

from nova.utils.display import console, stats_table, info


def get_system_info() -> dict:
    """Gather comprehensive system information."""
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return {
        "hostname": platform.node(),
        "os": f"{platform.system()} {platform.release()}",
        "architecture": platform.machine(),
        "python": platform.python_version(),
        "cpu_cores": psutil.cpu_count(logical=False),
        "cpu_threads": psutil.cpu_count(logical=True),
        "cpu_usage": f"{psutil.cpu_percent(interval=1)}%",
        "memory_total": _humanize(mem.total),
        "memory_used": f"{_humanize(mem.used)} ({mem.percent}%)",
        "memory_available": _humanize(mem.available),
        "disk_total": _humanize(disk.total),
        "disk_used": f"{_humanize(disk.used)} ({disk.percent}%)",
        "disk_free": _humanize(disk.free),
        "uptime": _format_uptime(),
    }


def show_system_info():
    """Display system information."""
    info_data = get_system_info()
    console.print(stats_table(info_data, title="System Information"))


def get_running_processes(sort_by: str = "memory", limit: int = 15) -> list[dict]:
    """Get top processes by resource usage."""
    processes = []
    for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "status"]):
        try:
            pinfo = proc.info
            processes.append({
                "pid": pinfo["pid"],
                "name": pinfo["name"][:30],
                "cpu": f"{pinfo['cpu_percent']:.1f}%",
                "memory": f"{pinfo['memory_percent']:.1f}%",
                "status": pinfo["status"],
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    key = "memory_percent" if sort_by == "memory" else "cpu_percent"
    # Sort by numeric value
    if sort_by == "memory":
        processes.sort(key=lambda p: float(p["memory"].rstrip("%")), reverse=True)
    else:
        processes.sort(key=lambda p: float(p["cpu"].rstrip("%")), reverse=True)

    return processes[:limit]


def show_processes(sort_by: str = "memory", limit: int = 15):
    """Display top processes."""
    from rich.table import Table

    procs = get_running_processes(sort_by, limit)
    table = Table(title=f"Top {limit} Processes (by {sort_by})")
    table.add_column("PID", style="dim", justify="right")
    table.add_column("Name", style="white")
    table.add_column("CPU", style="cyan", justify="right")
    table.add_column("Memory", style="green", justify="right")
    table.add_column("Status", style="yellow")

    for p in procs:
        table.add_row(str(p["pid"]), p["name"], p["cpu"], p["memory"], p["status"])

    console.print(table)


def get_disk_usage() -> list[dict]:
    """Get disk usage for all mounted partitions."""
    partitions = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            partitions.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "fstype": part.fstype,
                "total": _humanize(usage.total),
                "used": _humanize(usage.used),
                "free": _humanize(usage.free),
                "percent": f"{usage.percent}%",
            })
        except (PermissionError, OSError):
            continue
    return partitions


def show_disk_usage():
    """Display disk usage."""
    from rich.table import Table

    disks = get_disk_usage()
    table = Table(title="Disk Usage")
    table.add_column("Device", style="white")
    table.add_column("Mount", style="cyan")
    table.add_column("Type", style="dim")
    table.add_column("Total", justify="right")
    table.add_column("Used", justify="right")
    table.add_column("Free", justify="right", style="green")
    table.add_column("Usage", justify="right")

    for d in disks:
        pct = float(d["percent"].rstrip("%"))
        style = "red" if pct > 90 else "yellow" if pct > 75 else "green"
        table.add_row(
            d["device"], d["mountpoint"], d["fstype"],
            d["total"], d["used"], d["free"],
            f"[{style}]{d['percent']}[/{style}]"
        )

    console.print(table)


def find_large_files(directory: str = "~", min_size_mb: int = 100, limit: int = 20) -> list[dict]:
    """Find large files in a directory."""
    target = Path(directory).expanduser().resolve()
    large_files = []

    min_bytes = min_size_mb * 1024 * 1024
    for root, dirs, files in os.walk(target):
        # Skip hidden and system directories
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in {"node_modules", "__pycache__", ".git"}]
        for name in files:
            filepath = Path(root) / name
            try:
                size = filepath.stat().st_size
                if size >= min_bytes:
                    large_files.append({
                        "name": name,
                        "path": str(filepath),
                        "size": size,
                        "size_human": _humanize(size),
                        "modified": datetime.fromtimestamp(filepath.stat().st_mtime).strftime("%Y-%m-%d"),
                    })
            except (PermissionError, OSError):
                continue

    large_files.sort(key=lambda f: f["size"], reverse=True)
    return large_files[:limit]


def cleanup_suggestions() -> dict:
    """Generate cleanup suggestions."""
    suggestions = {
        "trash": _get_trash_size(),
        "caches": _find_caches(),
        "large_files": find_large_files(min_size_mb=500, limit=5),
        "temp_files": _count_temp_files(),
    }
    return suggestions


def _humanize(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def _format_uptime() -> str:
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.now() - boot_time
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    return " ".join(parts)


def _get_trash_size() -> str:
    """Estimate trash size."""
    trash_paths = [
        Path.home() / ".local/share/Trash",
        Path.home() / ".Trash",
    ]
    total = 0
    for tp in trash_paths:
        if tp.exists():
            for f in tp.rglob("*"):
                try:
                    total += f.stat().st_size
                except (PermissionError, OSError):
                    continue
    return _humanize(total)


def _find_caches() -> list[dict]:
    """Find common cache directories."""
    cache_dirs = [
        ("npm cache", Path.home() / ".npm/_cacache"),
        ("pip cache", Path.home() / ".cache/pip"),
        ("yarn cache", Path.home() / ".cache/yarn"),
        ("apt cache", Path("/var/cache/apt/archives")),
        ("thumbnails", Path.home() / ".cache/thumbnails"),
    ]
    results = []
    for name, path in cache_dirs:
        if path.exists():
            size = sum(
                f.stat().st_size for f in path.rglob("*") if f.is_file()
            ) if path.is_dir() else 0
            if size > 0:
                results.append({"name": name, "path": str(path), "size": _humanize(size)})
    return results


def _count_temp_files() -> int:
    """Count temporary files."""
    count = 0
    tmp_dirs = [Path("/tmp"), Path.home() / ".cache"]
    for td in tmp_dirs:
        if td.exists():
            try:
                count += sum(1 for _ in td.iterdir() if _.is_file())
            except PermissionError:
                continue
    return count
