"""Clipboard manager — history, search, and smart paste."""

import json
import time
from datetime import datetime
from pathlib import Path

from nova.config import DEFAULT_CONFIG_DIR
from nova.utils.display import console, success, info, warning, error, section_header

CLIPBOARD_HISTORY_FILE = DEFAULT_CONFIG_DIR / "clipboard_history.json"
MAX_HISTORY = 100


def _load_history() -> list[dict]:
    """Load clipboard history from disk."""
    if CLIPBOARD_HISTORY_FILE.exists():
        try:
            return json.loads(CLIPBOARD_HISTORY_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return []
    return []


def _save_history(history: list[dict]):
    """Save clipboard history to disk."""
    DEFAULT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CLIPBOARD_HISTORY_FILE.write_text(json.dumps(history[-MAX_HISTORY:], indent=2))


def _get_clipboard() -> str | None:
    """Get current clipboard content."""
    import subprocess
    try:
        # Try xclip (Linux)
        result = subprocess.run(["xclip", "-selection", "clipboard", "-o"],
                                capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return result.stdout
    except FileNotFoundError:
        pass
    try:
        # Try xsel (Linux fallback)
        result = subprocess.run(["xsel", "--clipboard", "--output"],
                                capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return result.stdout
    except FileNotFoundError:
        pass
    try:
        # Try pbpaste (macOS)
        result = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return result.stdout
    except FileNotFoundError:
        pass
    try:
        # Try wl-paste (Wayland)
        result = subprocess.run(["wl-paste"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return result.stdout
    except FileNotFoundError:
        pass
    return None


def _set_clipboard(text: str) -> bool:
    """Set clipboard content."""
    import subprocess
    commands = [
        ["xclip", "-selection", "clipboard"],
        ["xsel", "--clipboard", "--input"],
        ["pbcopy"],
        ["wl-copy"],
    ]
    for cmd in commands:
        try:
            subprocess.run(cmd, input=text, text=True, timeout=5)
            return True
        except FileNotFoundError:
            continue
    return False


def capture_clipboard():
    """Capture current clipboard to history."""
    content = _get_clipboard()
    if not content or not content.strip():
        warning("Clipboard is empty")
        return

    history = _load_history()
    entry = {
        "content": content[:2000],  # Limit entry size
        "timestamp": datetime.now().isoformat(),
        "preview": content[:80].replace("\n", " "),
        "length": len(content),
    }

    # Don't duplicate last entry
    if history and history[-1]["content"] == content:
        info("Already in history")
        return

    history.append(entry)
    _save_history(history)
    success(f"Saved to clipboard history ({len(content)} chars)")


def show_history(limit: int = 20):
    """Display clipboard history."""
    from rich.table import Table

    history = _load_history()
    if not history:
        info("Clipboard history is empty. Use '/clip save' to capture.")
        return

    section_header("Clipboard History")
    table = Table(show_lines=False, border_style="dim cyan", header_style="bold cyan")
    table.add_column("#", style="dim", justify="right", width=4)
    table.add_column("Preview", style="white")
    table.add_column("Length", style="cyan", justify="right")
    table.add_column("Time", style="dim")

    for i, entry in enumerate(reversed(history[-limit:]), 1):
        ts = datetime.fromisoformat(entry["timestamp"]).strftime("%H:%M %b %d")
        table.add_row(str(i), entry["preview"], str(entry["length"]), ts)

    console.print(table)


def search_history(query: str) -> list[dict]:
    """Search clipboard history."""
    history = _load_history()
    results = [e for e in history if query.lower() in e["content"].lower()]
    return results


def paste_from_history(index: int):
    """Paste an item from history to clipboard."""
    history = _load_history()
    if not history:
        warning("Clipboard history is empty")
        return

    # Convert from 1-based reverse index
    idx = len(history) - index
    if idx < 0 or idx >= len(history):
        error(f"Invalid index: {index}. History has {len(history)} items.")
        return

    entry = history[idx]
    if _set_clipboard(entry["content"]):
        success(f"Copied to clipboard: {entry['preview']}")
    else:
        error("Failed to set clipboard. No clipboard tool found.")


def clear_history():
    """Clear clipboard history."""
    _save_history([])
    success("Clipboard history cleared")
