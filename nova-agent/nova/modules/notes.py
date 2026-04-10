"""Quick notes and bookmarks module."""

import json
from datetime import datetime
from pathlib import Path

from nova.config import DEFAULT_CONFIG_DIR
from nova.utils.display import console, success, info, warning, error, section_header

NOTES_FILE = DEFAULT_CONFIG_DIR / "notes.json"
BOOKMARKS_FILE = DEFAULT_CONFIG_DIR / "bookmarks.json"


def _load_json(filepath: Path) -> list:
    if filepath.exists():
        try:
            return json.loads(filepath.read_text())
        except (json.JSONDecodeError, OSError):
            return []
    return []


def _save_json(filepath: Path, data: list):
    DEFAULT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    filepath.write_text(json.dumps(data, indent=2))


# ─── Notes ──────────────────────────────────────────────────────────

def add_note(content: str, tags: list[str] | None = None):
    """Add a quick note."""
    notes = _load_json(NOTES_FILE)
    note = {
        "id": len(notes) + 1,
        "content": content,
        "tags": tags or [],
        "created": datetime.now().isoformat(),
    }
    notes.append(note)
    _save_json(NOTES_FILE, notes)
    success(f"Note #{note['id']} saved")


def show_notes(tag_filter: str | None = None, limit: int = 20):
    """Display saved notes."""
    from rich.table import Table

    notes = _load_json(NOTES_FILE)
    if tag_filter:
        notes = [n for n in notes if tag_filter.lower() in [t.lower() for t in n.get("tags", [])]]

    if not notes:
        info("No notes found. Use '/note <text>' to add one.")
        return

    section_header("Notes")
    table = Table(border_style="dim cyan", header_style="bold cyan")
    table.add_column("#", style="dim", justify="right", width=4)
    table.add_column("Note", style="white")
    table.add_column("Tags", style="magenta")
    table.add_column("Created", style="dim")

    for note in reversed(notes[-limit:]):
        tags = ", ".join(note.get("tags", [])) or "—"
        created = datetime.fromisoformat(note["created"]).strftime("%H:%M %b %d")
        table.add_row(str(note["id"]), note["content"][:80], tags, created)

    console.print(table)


def delete_note(note_id: int):
    """Delete a note by ID."""
    notes = _load_json(NOTES_FILE)
    notes = [n for n in notes if n["id"] != note_id]
    _save_json(NOTES_FILE, notes)
    success(f"Note #{note_id} deleted")


def search_notes(query: str) -> list[dict]:
    """Search notes by content."""
    notes = _load_json(NOTES_FILE)
    return [n for n in notes if query.lower() in n["content"].lower()]


# ─── Bookmarks ──────────────────────────────────────────────────────

def add_bookmark(path: str, label: str | None = None):
    """Bookmark a file or directory path for quick access."""
    resolved = str(Path(path).expanduser().resolve())
    bookmarks = _load_json(BOOKMARKS_FILE)

    bookmark = {
        "path": resolved,
        "label": label or Path(resolved).name,
        "created": datetime.now().isoformat(),
        "type": "dir" if Path(resolved).is_dir() else "file",
    }

    # Don't duplicate
    if any(b["path"] == resolved for b in bookmarks):
        warning(f"Already bookmarked: {resolved}")
        return

    bookmarks.append(bookmark)
    _save_json(BOOKMARKS_FILE, bookmarks)
    success(f"Bookmarked: {bookmark['label']} ({resolved})")


def show_bookmarks():
    """Display saved bookmarks."""
    from rich.table import Table

    bookmarks = _load_json(BOOKMARKS_FILE)
    if not bookmarks:
        info("No bookmarks. Use '/bookmark <path>' to add one.")
        return

    section_header("Bookmarks")
    table = Table(border_style="dim cyan", header_style="bold cyan")
    table.add_column("#", style="dim", justify="right", width=4)
    table.add_column("Label", style="cyan")
    table.add_column("Path", style="white")
    table.add_column("Type", style="dim")
    table.add_column("Exists", style="green")

    for i, b in enumerate(bookmarks, 1):
        exists = "[green]✓[/]" if Path(b["path"]).exists() else "[red]✗[/]"
        table.add_row(str(i), b["label"], b["path"], b["type"], exists)

    console.print(table)


def remove_bookmark(index: int):
    """Remove a bookmark by index."""
    bookmarks = _load_json(BOOKMARKS_FILE)
    if 1 <= index <= len(bookmarks):
        removed = bookmarks.pop(index - 1)
        _save_json(BOOKMARKS_FILE, bookmarks)
        success(f"Removed bookmark: {removed['label']}")
    else:
        error(f"Invalid bookmark index: {index}")
