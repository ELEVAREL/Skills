"""Dotfile and environment manager — backup, restore, and audit configs."""

import os
import shutil
from pathlib import Path
from datetime import datetime

from nova.config import DEFAULT_CONFIG_DIR
from nova.utils.display import (
    console, success, info, warning, error, section_header,
    summary_panel, task_progress,
)

BACKUP_DIR = DEFAULT_CONFIG_DIR / "dotfile_backups"

COMMON_DOTFILES = [
    ".bashrc", ".bash_profile", ".zshrc", ".zprofile",
    ".gitconfig", ".gitignore_global",
    ".vimrc", ".tmux.conf",
    ".ssh/config",
    ".config/starship.toml",
    ".npmrc", ".yarnrc",
    ".pypirc", ".condarc",
    ".docker/config.json",
    ".kube/config",
    ".aws/config", ".aws/credentials",
]

SHELL_ENV_FILES = [".bashrc", ".bash_profile", ".zshrc", ".zprofile", ".profile"]


def find_dotfiles(home: str = "~") -> list[dict]:
    """Find all dotfiles in the home directory."""
    home_path = Path(home).expanduser()
    found = []

    for dotfile in COMMON_DOTFILES:
        filepath = home_path / dotfile
        if filepath.exists():
            try:
                stat = filepath.stat()
                found.append({
                    "name": dotfile,
                    "path": str(filepath),
                    "size": _humanize(stat.st_size),
                    "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d"),
                })
            except (PermissionError, OSError):
                continue

    return found


def show_dotfiles():
    """Display found dotfiles."""
    from rich.table import Table

    section_header("Dotfiles")
    dotfiles = find_dotfiles()

    if not dotfiles:
        info("No common dotfiles found")
        return

    table = Table(border_style="dim cyan", header_style="bold cyan")
    table.add_column("File", style="cyan")
    table.add_column("Size", style="white", justify="right")
    table.add_column("Last Modified", style="dim")

    for d in dotfiles:
        table.add_row(d["name"], d["size"], d["modified"])

    console.print(table)
    info(f"Found {len(dotfiles)} dotfiles")


def backup_dotfiles():
    """Backup all found dotfiles to ~/.nova/dotfile_backups/."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / timestamp
    backup_path.mkdir(parents=True, exist_ok=True)

    dotfiles = find_dotfiles()
    if not dotfiles:
        warning("No dotfiles to backup")
        return

    backed_up = 0
    with task_progress("Backing up") as progress:
        task = progress.add_task("Backing up dotfiles", total=len(dotfiles))
        for d in dotfiles:
            src = Path(d["path"])
            dst = backup_path / d["name"]
            dst.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(str(src), str(dst))
                backed_up += 1
            except (PermissionError, OSError) as e:
                warning(f"Failed to backup {d['name']}: {e}")
            progress.update(task, advance=1)

    success(f"Backed up {backed_up} dotfiles to {backup_path}")


def list_backups():
    """List available dotfile backups."""
    from rich.table import Table

    if not BACKUP_DIR.exists():
        info("No backups found. Use '/dotfiles backup' to create one.")
        return

    backups = sorted(BACKUP_DIR.iterdir(), reverse=True)
    if not backups:
        info("No backups found")
        return

    section_header("Dotfile Backups")
    table = Table(border_style="dim cyan", header_style="bold cyan")
    table.add_column("#", style="dim", justify="right", width=4)
    table.add_column("Backup", style="cyan")
    table.add_column("Files", style="white", justify="right")
    table.add_column("Size", style="dim")

    for i, backup in enumerate(backups, 1):
        files = list(backup.rglob("*"))
        file_count = sum(1 for f in files if f.is_file())
        total_size = sum(f.stat().st_size for f in files if f.is_file())
        table.add_row(str(i), backup.name, str(file_count), _humanize(total_size))

    console.print(table)


def get_shell_aliases() -> list[dict]:
    """Extract aliases from shell config files."""
    home = Path.home()
    aliases = []

    for shell_file in SHELL_ENV_FILES:
        filepath = home / shell_file
        if filepath.exists():
            try:
                for line in filepath.read_text().splitlines():
                    stripped = line.strip()
                    if stripped.startswith("alias ") and "=" in stripped:
                        parts = stripped[6:].split("=", 1)
                        if len(parts) == 2:
                            name = parts[0].strip()
                            value = parts[1].strip().strip("'\"")
                            aliases.append({
                                "name": name,
                                "command": value[:80],
                                "source": shell_file,
                            })
            except (PermissionError, OSError):
                continue

    return aliases


def show_aliases():
    """Display shell aliases."""
    from rich.table import Table

    aliases = get_shell_aliases()
    if not aliases:
        info("No shell aliases found")
        return

    section_header("Shell Aliases")
    table = Table(border_style="dim cyan", header_style="bold cyan")
    table.add_column("Alias", style="cyan")
    table.add_column("Command", style="white")
    table.add_column("Source", style="dim")

    for a in aliases:
        table.add_row(a["name"], a["command"], a["source"])

    console.print(table)
    info(f"Found {len(aliases)} aliases")


def get_env_vars(filter_prefix: str = "") -> dict:
    """Get environment variables, optionally filtered."""
    env = dict(os.environ)
    if filter_prefix:
        env = {k: v for k, v in env.items() if k.startswith(filter_prefix.upper())}
    # Mask sensitive values
    sensitive = {"KEY", "SECRET", "TOKEN", "PASSWORD", "CREDENTIAL", "AUTH"}
    masked = {}
    for k, v in sorted(env.items()):
        if any(s in k.upper() for s in sensitive):
            masked[k] = v[:4] + "****" if len(v) > 4 else "****"
        else:
            masked[k] = v[:80]
    return masked


def show_env(prefix: str = ""):
    """Display environment variables."""
    from rich.table import Table

    env = get_env_vars(prefix)
    title = f"Environment Variables ({prefix}*)" if prefix else "Environment Variables"

    section_header(title)
    table = Table(border_style="dim cyan", header_style="bold cyan")
    table.add_column("Variable", style="cyan")
    table.add_column("Value", style="white", max_width=60)

    for k, v in list(env.items())[:50]:
        table.add_row(k, v)

    console.print(table)
    info(f"Showing {min(len(env), 50)} of {len(env)} variables")


def _humanize(b: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} TB"
