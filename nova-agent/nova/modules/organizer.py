"""File organizer module — scan, categorize, and organize files."""

import os
import shutil
from pathlib import Path
from datetime import datetime
from collections import defaultdict

from nova.config import load_organize_rules
from nova.utils.display import (
    console, success, warning, info, error, file_table, stats_table,
    scan_progress, section_header, summary_panel, completion_animation,
)


def humanize_size(size_bytes: int) -> str:
    """Convert bytes to human-readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def categorize_file(filepath: Path, rules: dict) -> str:
    """Determine the category for a file based on its extension."""
    ext = filepath.suffix.lower()
    # Handle compound extensions like .tar.gz
    if filepath.name.endswith(".tar.gz"):
        ext = ".tar.gz"

    for category, config in rules.get("categories", {}).items():
        if ext in config.get("extensions", []):
            return category
    return "Other"


def scan_directory(target: str, recursive: bool = False, show_hidden: bool = False) -> list[dict]:
    """Scan a directory and categorize all files."""
    target_path = Path(target).expanduser().resolve()
    if not target_path.is_dir():
        error(f"Not a directory: {target_path}")
        return []

    rules = load_organize_rules()
    files = []

    if recursive:
        all_entries = list(target_path.rglob("*"))
    else:
        all_entries = list(target_path.iterdir())

    file_entries = [e for e in all_entries if e.is_file() and (show_hidden or not e.name.startswith("."))]

    with scan_progress("Scanning files") as progress:
        task = progress.add_task("Scanning files", total=len(file_entries))
        for entry in file_entries:
            try:
                stat = entry.stat()
                category = categorize_file(entry, rules)
                files.append({
                    "name": entry.name,
                    "path": str(entry),
                    "extension": entry.suffix.lower(),
                    "size": stat.st_size,
                    "size_human": humanize_size(stat.st_size),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "category": category,
                    "action": "",
                })
            except (PermissionError, OSError):
                pass
            progress.update(task, advance=1)

    return sorted(files, key=lambda f: (f["category"], f["name"]))


def analyze_directory(target: str, recursive: bool = False) -> dict:
    """Analyze a directory and return statistics."""
    files = scan_directory(target, recursive)

    stats = {
        "total_files": len(files),
        "total_size": humanize_size(sum(f["size"] for f in files)),
        "categories": defaultdict(lambda: {"count": 0, "size": 0}),
        "largest_files": [],
        "duplicates": [],
        "old_files": [],
    }

    # Category breakdown
    for f in files:
        cat = f["category"]
        stats["categories"][cat]["count"] += 1
        stats["categories"][cat]["size"] += f["size"]

    # Top 10 largest files
    stats["largest_files"] = sorted(files, key=lambda f: f["size"], reverse=True)[:10]

    # Files not modified in 90+ days
    cutoff = datetime.now().timestamp() - (90 * 24 * 3600)
    for f in files:
        fpath = Path(f["path"])
        try:
            if fpath.stat().st_mtime < cutoff:
                stats["old_files"].append(f)
        except (PermissionError, OSError):
            continue

    # Detect duplicates by name
    name_counts = defaultdict(list)
    for f in files:
        name_counts[f["name"]].append(f)
    stats["duplicates"] = [
        {"name": name, "copies": len(paths), "locations": [p["path"] for p in paths]}
        for name, paths in name_counts.items()
        if len(paths) > 1
    ]

    return stats


def organize_files(
    source: str,
    destination: str | None = None,
    dry_run: bool = True,
    recursive: bool = False,
) -> list[dict]:
    """Organize files from source directory into categorized folders.

    Args:
        source: Directory to organize
        destination: Where to create organized folders (defaults to source)
        dry_run: If True, only show what would happen without moving files
        recursive: Include subdirectories
    """
    source_path = Path(source).expanduser().resolve()
    dest_path = Path(destination).expanduser().resolve() if destination else source_path

    if not source_path.is_dir():
        error(f"Source is not a directory: {source_path}")
        return []

    rules = load_organize_rules()
    files = scan_directory(source, recursive)
    actions = []

    for f in files:
        category = f["category"]
        if category == "Other":
            f["action"] = "skip (unknown type)"
            actions.append(f)
            continue

        cat_config = rules.get("categories", {}).get(category, {})
        target_folder = dest_path / cat_config.get("folder", category)
        target_file = target_folder / f["name"]
        source_file = Path(f["path"])

        # Skip if already in the right place
        if source_file.parent == target_folder:
            f["action"] = "already organized"
            actions.append(f)
            continue

        # Handle naming conflicts
        if target_file.exists():
            stem = target_file.stem
            suffix = target_file.suffix
            counter = 1
            while target_file.exists():
                target_file = target_folder / f"{stem}_{counter}{suffix}"
                counter += 1

        f["action"] = f"→ {target_folder.name}/"
        f["target"] = str(target_file)

        if not dry_run:
            try:
                target_folder.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source_file), str(target_file))
                f["action"] = f"✓ moved → {target_folder.name}/"
            except (PermissionError, OSError) as e:
                f["action"] = f"✗ error: {e}"

        actions.append(f)

    return actions


def show_analysis(target: str, recursive: bool = False):
    """Display a rich analysis of a directory with animations."""
    section_header(f"Analyzing: {target}")

    stats = analyze_directory(target, recursive)

    # Summary panel
    summary_panel("Directory Summary", {
        "Total Files": str(stats["total_files"]),
        "Total Size": stats["total_size"],
        "Categories": str(len(stats["categories"])),
        "Duplicate Names": str(len(stats["duplicates"])),
        "Stale Files (90+ days)": str(len(stats["old_files"])),
    })

    # Category breakdown
    cat_table_data = {
        f"{cat} ({data['count']} files)": humanize_size(data["size"])
        for cat, data in sorted(stats["categories"].items(), key=lambda x: x[1]["size"], reverse=True)
    }
    if cat_table_data:
        console.print()
        console.print(stats_table(cat_table_data, title="Breakdown by Category"))

    # Largest files
    if stats["largest_files"]:
        console.print()
        console.print(file_table(stats["largest_files"][:10], title="Top 10 Largest Files"))

    # Duplicates
    if stats["duplicates"]:
        console.print()
        warning(f"Found {len(stats['duplicates'])} files with duplicate names")
        for dup in stats["duplicates"][:5]:
            console.print(f"    [yellow]{dup['name']}[/] — {dup['copies']} copies")

    completion_animation("Analysis complete!")
    return stats
