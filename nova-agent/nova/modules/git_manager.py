"""Git repository manager — status, branches, stats across all repos."""

import os
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from nova.utils.display import (
    console, success, info, warning, error, section_header,
    task_progress, summary_panel,
)


def _run_git(repo_path: str, *args) -> tuple[str, bool]:
    """Run a git command in a repo directory."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=repo_path,
            capture_output=True, text=True, timeout=10,
        )
        return result.stdout.strip(), result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return "", False


def find_repos(root: str = "~", max_depth: int = 3) -> list[str]:
    """Find all git repositories under a directory."""
    root_path = Path(root).expanduser().resolve()
    repos = []

    skip_dirs = {".git", "node_modules", "__pycache__", ".venv", "venv", ".cache", ".npm"}

    def _scan(path: Path, depth: int):
        if depth > max_depth:
            return
        try:
            for entry in path.iterdir():
                if entry.name in skip_dirs:
                    if entry.name == ".git" and entry.is_dir():
                        repos.append(str(path))
                    continue
                if entry.is_dir() and not entry.is_symlink():
                    _scan(entry, depth + 1)
        except (PermissionError, OSError):
            pass

    _scan(root_path, 0)
    return repos


def get_repo_status(repo_path: str) -> dict:
    """Get comprehensive status for a git repo."""
    name = Path(repo_path).name

    branch, _ = _run_git(repo_path, "branch", "--show-current")
    status_out, _ = _run_git(repo_path, "status", "--porcelain")
    last_commit, _ = _run_git(repo_path, "log", "-1", "--format=%s (%ar)")
    remote, _ = _run_git(repo_path, "remote", "-v")
    ahead_behind, _ = _run_git(repo_path, "rev-list", "--left-right", "--count", f"HEAD...@{{u}}")

    changes = len([l for l in status_out.splitlines() if l.strip()]) if status_out else 0

    ahead, behind = 0, 0
    if ahead_behind:
        parts = ahead_behind.split()
        if len(parts) == 2:
            ahead, behind = int(parts[0]), int(parts[1])

    dirty = changes > 0
    has_remote = bool(remote)

    return {
        "name": name,
        "path": repo_path,
        "branch": branch or "unknown",
        "changes": changes,
        "dirty": dirty,
        "last_commit": last_commit or "no commits",
        "ahead": ahead,
        "behind": behind,
        "has_remote": has_remote,
    }


def show_repo_status(repo_path: str = "."):
    """Display detailed status for a single repo."""
    repo = Path(repo_path).expanduser().resolve()
    status = get_repo_status(str(repo))

    section_header(f"Repository: {status['name']}")

    dirty_str = "[red]dirty[/]" if status["dirty"] else "[green]clean[/]"
    sync_parts = []
    if status["ahead"] > 0:
        sync_parts.append(f"[yellow]{status['ahead']} ahead[/]")
    if status["behind"] > 0:
        sync_parts.append(f"[red]{status['behind']} behind[/]")
    sync_str = ", ".join(sync_parts) if sync_parts else "[green]in sync[/]"

    summary_panel("Git Status", {
        "Branch": status["branch"],
        "Status": dirty_str,
        "Uncommitted changes": str(status["changes"]),
        "Remote sync": sync_str,
        "Last commit": status["last_commit"],
        "Path": status["path"],
    })


def show_all_repos(root: str = "~", max_depth: int = 3):
    """Find and display status of all git repos."""
    from rich.table import Table

    section_header("Git Repositories")
    info(f"Scanning {root} (depth: {max_depth})...")

    repos = find_repos(root, max_depth)
    if not repos:
        warning("No git repositories found")
        return

    info(f"Found {len(repos)} repositories. Checking status...")

    statuses = []
    with task_progress("Checking repos") as progress:
        task = progress.add_task("Scanning", total=len(repos))
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(get_repo_status, r): r for r in repos}
            for future in as_completed(futures):
                statuses.append(future.result())
                progress.update(task, advance=1)

    statuses.sort(key=lambda s: s["name"])

    table = Table(title=f"Git Repositories ({len(repos)})",
                  border_style="dim cyan", header_style="bold cyan")
    table.add_column("Repository", style="white")
    table.add_column("Branch", style="cyan")
    table.add_column("Changes", justify="right")
    table.add_column("Sync", style="dim")
    table.add_column("Last Commit", style="dim", max_width=40)

    for s in statuses:
        changes = f"[red]{s['changes']}[/]" if s["changes"] > 0 else "[green]0[/]"
        sync_parts = []
        if s["ahead"] > 0:
            sync_parts.append(f"↑{s['ahead']}")
        if s["behind"] > 0:
            sync_parts.append(f"↓{s['behind']}")
        sync = " ".join(sync_parts) if sync_parts else "✓"
        table.add_row(s["name"], s["branch"], changes, sync, s["last_commit"])

    console.print(table)

    dirty = sum(1 for s in statuses if s["dirty"])
    if dirty > 0:
        console.print()
        warning(f"{dirty} repositories have uncommitted changes")


def show_git_stats(repo_path: str = "."):
    """Show git statistics for a repository."""
    repo = Path(repo_path).expanduser().resolve()

    section_header("Git Statistics")

    # Commit count
    count, _ = _run_git(str(repo), "rev-list", "--count", "HEAD")

    # Contributors
    contributors, _ = _run_git(str(repo), "shortlog", "-sn", "--no-merges", "HEAD")
    contrib_count = len(contributors.splitlines()) if contributors else 0

    # File stats
    files, _ = _run_git(str(repo), "ls-files")
    file_count = len(files.splitlines()) if files else 0

    # Date range
    first_commit, _ = _run_git(str(repo), "log", "--reverse", "--format=%ai", "-1")
    last_commit, _ = _run_git(str(repo), "log", "--format=%ai", "-1")

    summary_panel("Repository Statistics", {
        "Total commits": count or "0",
        "Contributors": str(contrib_count),
        "Tracked files": str(file_count),
        "First commit": first_commit[:10] if first_commit else "N/A",
        "Latest commit": last_commit[:10] if last_commit else "N/A",
    })

    # Top contributors
    if contributors:
        from rich.table import Table
        table = Table(title="Top Contributors", border_style="dim cyan", header_style="bold cyan")
        table.add_column("Commits", style="cyan", justify="right")
        table.add_column("Author", style="white")
        for line in contributors.splitlines()[:10]:
            parts = line.strip().split("\t", 1)
            if len(parts) == 2:
                table.add_row(parts[0].strip(), parts[1].strip())
        console.print(table)
