"""Duplicate file finder — by content hash, not just name."""

import hashlib
import os
from collections import defaultdict
from pathlib import Path

from nova.utils.display import (
    console, success, info, warning, error, section_header,
    task_progress, summary_panel,
)


def _hash_file(filepath: Path, chunk_size: int = 8192) -> str:
    """Calculate SHA-256 hash of a file (fast: reads in chunks)."""
    hasher = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
        return hasher.hexdigest()
    except (PermissionError, OSError):
        return ""


def _quick_hash(filepath: Path) -> str:
    """Quick hash using first and last 4KB (for pre-filtering)."""
    hasher = hashlib.md5()
    try:
        size = filepath.stat().st_size
        with open(filepath, "rb") as f:
            hasher.update(f.read(4096))
            if size > 8192:
                f.seek(-4096, 2)
                hasher.update(f.read(4096))
        return hasher.hexdigest()
    except (PermissionError, OSError):
        return ""


def find_duplicates(
    directory: str,
    min_size: int = 1024,  # Ignore files < 1KB
    recursive: bool = True,
) -> list[dict]:
    """Find duplicate files by content hash.

    Uses a 3-phase approach for speed:
    1. Group by file size (different sizes can't be duplicates)
    2. Quick hash (first+last 4KB) to filter further
    3. Full SHA-256 hash to confirm
    """
    root = Path(directory).expanduser().resolve()
    skip = {".git", "node_modules", "__pycache__", ".venv", "venv", ".cache", "dist", "build"}

    # Phase 1: Group by size
    size_groups = defaultdict(list)
    file_count = 0

    for dirpath, dirnames, filenames in os.walk(root):
        if not recursive and dirpath != str(root):
            continue
        dirnames[:] = [d for d in dirnames if d not in skip and not d.startswith(".")]
        for name in filenames:
            filepath = Path(dirpath) / name
            try:
                size = filepath.stat().st_size
                if size >= min_size:
                    size_groups[size].append(filepath)
                    file_count += 1
            except (PermissionError, OSError):
                continue

    # Only keep sizes with multiple files
    potential = {s: files for s, files in size_groups.items() if len(files) > 1}
    potential_count = sum(len(f) for f in potential.values())

    if not potential:
        return []

    # Phase 2: Quick hash
    quick_groups = defaultdict(list)
    with task_progress("Finding duplicates") as progress:
        task = progress.add_task("Quick scan", total=potential_count)
        for size, files in potential.items():
            for f in files:
                qhash = _quick_hash(f)
                if qhash:
                    quick_groups[(size, qhash)].append(f)
                progress.update(task, advance=1)

    # Phase 3: Full hash for confirmation
    confirmed = defaultdict(list)
    candidates = {k: v for k, v in quick_groups.items() if len(v) > 1}
    candidate_count = sum(len(v) for v in candidates.values())

    if candidate_count > 0:
        with task_progress("Confirming duplicates") as progress:
            task = progress.add_task("Full hash", total=candidate_count)
            for key, files in candidates.items():
                for f in files:
                    full_hash = _hash_file(f)
                    if full_hash:
                        confirmed[full_hash].append(f)
                    progress.update(task, advance=1)

    # Build results
    duplicates = []
    for hash_val, files in confirmed.items():
        if len(files) > 1:
            size = files[0].stat().st_size
            duplicates.append({
                "hash": hash_val[:12],
                "count": len(files),
                "size_each": _humanize(size),
                "wasted": _humanize(size * (len(files) - 1)),
                "files": [str(f) for f in files],
            })

    duplicates.sort(key=lambda d: int(d["count"]), reverse=True)
    return duplicates


def show_duplicates(directory: str = ".", min_size_kb: int = 1):
    """Display duplicate file analysis."""
    section_header(f"Duplicate File Scan: {directory}")

    info(f"Scanning for duplicate files (min size: {min_size_kb}KB)...")
    duplicates = find_duplicates(directory, min_size=min_size_kb * 1024)

    if not duplicates:
        success("No duplicate files found!")
        return

    from rich.table import Table

    total_wasted = sum(
        Path(d["files"][0]).stat().st_size * (d["count"] - 1)
        for d in duplicates
        if Path(d["files"][0]).exists()
    )

    summary_panel("Duplicate Summary", {
        "Duplicate groups": str(len(duplicates)),
        "Total duplicate files": str(sum(d["count"] - 1 for d in duplicates)),
        "Wasted space": _humanize(total_wasted),
    }, style="yellow")

    console.print()

    for i, dup in enumerate(duplicates[:20], 1):
        console.print(f"  [bold yellow]Group {i}[/] — {dup['count']} copies, {dup['size_each']} each "
                       f"([red]{dup['wasted']} wasted[/])")
        for f in dup["files"]:
            console.print(f"    [dim]{f}[/]")
        console.print()

    if len(duplicates) > 20:
        info(f"Showing 20 of {len(duplicates)} duplicate groups")


def _humanize(b: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} TB"
