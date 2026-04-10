"""File watcher module — auto-organize files as they arrive."""

import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from nova.config import load_organize_rules
from nova.modules.organizer import categorize_file, humanize_size
from nova.utils.display import console, success, info, warning


class AutoOrganizeHandler(FileSystemEventHandler):
    """Handler that auto-organizes new files."""

    def __init__(self, destination: str | None = None, dry_run: bool = False):
        self.rules = load_organize_rules()
        self.destination = destination
        self.dry_run = dry_run

    def on_created(self, event):
        if isinstance(event, FileCreatedEvent):
            filepath = Path(event.src_path)

            # Skip hidden files and temporary files
            if filepath.name.startswith(".") or filepath.name.endswith(".part"):
                return

            # Wait a moment for file to finish writing
            time.sleep(1)

            if not filepath.exists():
                return

            category = categorize_file(filepath, self.rules)
            if category == "Other":
                info(f"New file: {filepath.name} [dim](unknown type, skipping)[/]")
                return

            cat_config = self.rules.get("categories", {}).get(category, {})
            dest_base = Path(self.destination) if self.destination else filepath.parent
            target_folder = dest_base / cat_config.get("folder", category)
            target_file = target_folder / filepath.name

            size = humanize_size(filepath.stat().st_size)

            if self.dry_run:
                info(f"Would move: {filepath.name} ({size}) → {target_folder.name}/")
                return

            try:
                target_folder.mkdir(parents=True, exist_ok=True)

                # Handle conflicts
                if target_file.exists():
                    stem = target_file.stem
                    suffix = target_file.suffix
                    counter = 1
                    while target_file.exists():
                        target_file = target_folder / f"{stem}_{counter}{suffix}"
                        counter += 1

                import shutil
                shutil.move(str(filepath), str(target_file))
                success(f"Organized: {filepath.name} ({size}) → {target_folder.name}/")
            except (PermissionError, OSError) as e:
                warning(f"Failed to move {filepath.name}: {e}")


def watch_directory(
    directory: str,
    destination: str | None = None,
    dry_run: bool = False,
):
    """Watch a directory and auto-organize new files.

    Args:
        directory: Directory to watch
        destination: Where to organize files (defaults to same directory)
        dry_run: Only log what would happen
    """
    watch_path = Path(directory).expanduser().resolve()
    if not watch_path.is_dir():
        warning(f"Not a directory: {watch_path}")
        return

    handler = AutoOrganizeHandler(destination=destination or str(watch_path), dry_run=dry_run)
    observer = Observer()
    observer.schedule(handler, str(watch_path), recursive=False)
    observer.start()

    mode = "[yellow]dry-run[/]" if dry_run else "[green]live[/]"
    info(f"Watching {watch_path} ({mode})")
    info("Press Ctrl+C to stop")
    console.print()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        info("Watcher stopped.")
    observer.join()
