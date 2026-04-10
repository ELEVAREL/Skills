"""Smart search module — files, content, and command history."""

import os
import subprocess
from pathlib import Path
from datetime import datetime

from nova.utils.display import (
    console, success, info, warning, error, section_header,
    task_progress,
)


def search_files(query: str, directory: str = ".", max_results: int = 50) -> list[dict]:
    """Search for files by name pattern."""
    root = Path(directory).expanduser().resolve()
    results = []
    query_lower = query.lower()

    skip = {".git", "node_modules", "__pycache__", ".venv", "venv", ".cache", ".npm", "dist", "build"}

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip and not d.startswith(".")]
        for name in filenames:
            if query_lower in name.lower():
                filepath = Path(dirpath) / name
                try:
                    stat = filepath.stat()
                    results.append({
                        "name": name,
                        "path": str(filepath),
                        "size": _humanize(stat.st_size),
                        "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                    })
                except (PermissionError, OSError):
                    continue
                if len(results) >= max_results:
                    return results

    return results


def search_content(pattern: str, directory: str = ".", file_types: str = "",
                   max_results: int = 30) -> list[dict]:
    """Search file contents using grep/ripgrep."""
    root = Path(directory).expanduser().resolve()

    # Try ripgrep first (faster), then grep
    for cmd_name, cmd in [
        ("rg", ["rg", "--no-heading", "-n", "--max-count", "3", "-l",
                 "--max-filesize", "1M", pattern, str(root)]),
        ("grep", ["grep", "-rl", "--include=*.py", "--include=*.js",
                   "--include=*.ts", "--include=*.md", "--include=*.txt",
                   "--include=*.json", "--include=*.yaml", "--include=*.yml",
                   "-n", pattern, str(root)]),
    ]:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode in (0, 1):  # 1 = no matches for grep
                matches = []
                for line in result.stdout.strip().splitlines()[:max_results]:
                    filepath = Path(line.split(":")[0]) if ":" in line else Path(line)
                    if filepath.exists():
                        matches.append({
                            "file": filepath.name,
                            "path": str(filepath),
                            "match": line.strip()[:120],
                        })
                return matches
        except FileNotFoundError:
            continue
        except subprocess.TimeoutExpired:
            warning("Search timed out")
            return []

    # Fallback: Python-based search
    return _python_search(pattern, root, max_results)


def _python_search(pattern: str, root: Path, max_results: int) -> list[dict]:
    """Fallback content search using Python."""
    text_extensions = {".py", ".js", ".ts", ".jsx", ".tsx", ".md", ".txt",
                       ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini",
                       ".html", ".css", ".sh", ".bash", ".go", ".rs", ".java"}
    results = []
    skip = {".git", "node_modules", "__pycache__", ".venv", "dist", "build"}

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip]
        for name in filenames:
            if Path(name).suffix.lower() not in text_extensions:
                continue
            filepath = Path(dirpath) / name
            try:
                content = filepath.read_text(errors="ignore")
                for i, line in enumerate(content.splitlines(), 1):
                    if pattern.lower() in line.lower():
                        results.append({
                            "file": name,
                            "path": str(filepath),
                            "match": f"{i}: {line.strip()[:100]}",
                        })
                        break  # One match per file
                if len(results) >= max_results:
                    return results
            except (PermissionError, OSError):
                continue

    return results


def show_file_search(query: str, directory: str = "."):
    """Display file search results."""
    from rich.table import Table

    section_header(f"Search: {query}")
    results = search_files(query, directory)

    if not results:
        info("No files found")
        return

    table = Table(title=f"Files matching '{query}'",
                  border_style="dim cyan", header_style="bold cyan")
    table.add_column("#", style="dim", justify="right", width=4)
    table.add_column("File", style="white")
    table.add_column("Size", style="cyan", justify="right")
    table.add_column("Modified", style="dim")
    table.add_column("Path", style="dim", max_width=50)

    for i, r in enumerate(results, 1):
        table.add_row(str(i), r["name"], r["size"], r["modified"], r["path"])

    console.print(table)
    info(f"Found {len(results)} files")


def show_content_search(pattern: str, directory: str = "."):
    """Display content search results."""
    from rich.table import Table

    section_header(f"Content Search: {pattern}")
    with task_progress("Searching") as progress:
        task = progress.add_task("Searching files", total=1)
        results = search_content(pattern, directory)
        progress.update(task, advance=1)

    if not results:
        info("No matches found")
        return

    table = Table(title=f"Files containing '{pattern}'",
                  border_style="dim cyan", header_style="bold cyan")
    table.add_column("#", style="dim", justify="right", width=4)
    table.add_column("File", style="white")
    table.add_column("Match", style="dim", max_width=80)

    for i, r in enumerate(results, 1):
        table.add_row(str(i), r["file"], r["match"])

    console.print(table)
    info(f"Found {len(results)} matching files")


def find_recent(directory: str = ".", hours: int = 24, limit: int = 30) -> list[dict]:
    """Find recently modified files."""
    root = Path(directory).expanduser().resolve()
    cutoff = datetime.now().timestamp() - (hours * 3600)
    results = []
    skip = {".git", "node_modules", "__pycache__", ".venv", "dist"}

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip and not d.startswith(".")]
        for name in filenames:
            filepath = Path(dirpath) / name
            try:
                stat = filepath.stat()
                if stat.st_mtime > cutoff:
                    results.append({
                        "name": name,
                        "path": str(filepath),
                        "size": _humanize(stat.st_size),
                        "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                    })
            except (PermissionError, OSError):
                continue

    results.sort(key=lambda r: r["modified"], reverse=True)
    return results[:limit]


def show_recent(directory: str = ".", hours: int = 24):
    """Display recently modified files."""
    from rich.table import Table

    section_header(f"Recently Modified (last {hours}h)")
    results = find_recent(directory, hours)

    if not results:
        info("No recently modified files found")
        return

    table = Table(border_style="dim cyan", header_style="bold cyan")
    table.add_column("File", style="white")
    table.add_column("Size", style="cyan", justify="right")
    table.add_column("Modified", style="yellow")
    table.add_column("Path", style="dim", max_width=50)

    for r in results:
        table.add_row(r["name"], r["size"], r["modified"], r["path"])

    console.print(table)
    info(f"Found {len(results)} recently modified files")


def _humanize(b: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} TB"
