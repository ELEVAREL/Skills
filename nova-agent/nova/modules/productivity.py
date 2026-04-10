"""Productivity tracker — session stats, streaks, daily summary."""

import json
import time
from datetime import datetime, date, timedelta
from pathlib import Path

from nova.config import DEFAULT_CONFIG_DIR
from nova.utils.display import (
    console, section_header, summary_panel, nova_table, metric_cards, _mini_bar,
    success, info, muted,
)

TRACKER_FILE = DEFAULT_CONFIG_DIR / "productivity.json"


def _load_data() -> dict:
    if TRACKER_FILE.exists():
        try:
            return json.loads(TRACKER_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"sessions": [], "streak": 0, "last_active": None, "total_commands": 0}


def _save_data(data: dict):
    DEFAULT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    TRACKER_FILE.write_text(json.dumps(data, indent=2))


def track_session_start():
    """Record a session start."""
    data = _load_data()
    today = date.today().isoformat()

    # Update streak
    last = data.get("last_active")
    if last:
        last_date = date.fromisoformat(last)
        if last_date == date.today() - timedelta(days=1):
            data["streak"] = data.get("streak", 0) + 1
        elif last_date != date.today():
            data["streak"] = 1
    else:
        data["streak"] = 1

    data["last_active"] = today

    # Add session
    data["sessions"].append({
        "date": today,
        "start": datetime.now().isoformat(),
        "commands": 0,
    })

    # Keep last 90 days
    cutoff = (date.today() - timedelta(days=90)).isoformat()
    data["sessions"] = [s for s in data["sessions"] if s["date"] >= cutoff]

    _save_data(data)


def track_command():
    """Increment command counter for current session."""
    data = _load_data()
    data["total_commands"] = data.get("total_commands", 0) + 1
    if data["sessions"]:
        data["sessions"][-1]["commands"] = data["sessions"][-1].get("commands", 0) + 1
    _save_data(data)


def show_stats():
    """Display productivity statistics."""
    data = _load_data()

    section_header("Productivity Dashboard", icon="📈")

    streak = data.get("streak", 0)
    total_cmds = data.get("total_commands", 0)
    sessions = data.get("sessions", [])
    total_sessions = len(sessions)

    streak_color = "#00ff88" if streak >= 7 else "#ffbb33" if streak >= 3 else "#00d4ff"
    fire = "🔥" if streak >= 3 else "⚡"

    metric_cards([
        {"label": "Day Streak", "value": f"{fire} {streak}", "color": streak_color, "icon": "📅"},
        {"label": "Total Sessions", "value": str(total_sessions), "color": "#7b68ee", "icon": "💻"},
        {"label": "Commands Run", "value": f"{total_cmds:,}", "color": "#00d4ff", "icon": "⌨"},
        {"label": "Last Active", "value": data.get("last_active", "Never"), "color": "#ff6ec7", "icon": "🕐"},
    ])

    # Activity heatmap (last 14 days)
    if sessions:
        console.print()
        _show_activity_heatmap(sessions)

    # Daily breakdown (last 7 days)
    if sessions:
        console.print()
        _show_daily_breakdown(sessions)


def _show_activity_heatmap(sessions: list[dict]):
    """Show a simple activity heatmap for last 14 days."""
    from collections import Counter

    day_counts = Counter(s["date"] for s in sessions)

    today = date.today()
    days = [(today - timedelta(days=i)) for i in range(13, -1, -1)]

    heatmap_line = "  "
    for d in days:
        count = day_counts.get(d.isoformat(), 0)
        if count == 0:
            heatmap_line += "[dim]░[/]"
        elif count == 1:
            heatmap_line += "[#5b50ff]▓[/]"
        elif count <= 3:
            heatmap_line += "[#7b68ee]█[/]"
        else:
            heatmap_line += "[#00ff88]█[/]"
        heatmap_line += " "

    console.print("  [dim]Activity (14 days):[/]")
    console.print(heatmap_line)
    dates_line = "  " + "  ".join(d.strftime("%d") for d in days)
    muted(dates_line)


def _show_daily_breakdown(sessions: list[dict]):
    """Show daily breakdown for the last 7 days."""
    from collections import Counter

    day_counts = Counter()
    day_commands = Counter()
    for s in sessions:
        day_counts[s["date"]] += 1
        day_commands[s["date"]] += s.get("commands", 0)

    today = date.today()
    table = nova_table("Last 7 Days", [
        ("Date", "#00d4ff", {}),
        ("Sessions", "white", {"justify": "right"}),
        ("Commands", "#7b68ee", {"justify": "right"}),
        ("Activity", "#00ff88", {}),
    ])

    for i in range(6, -1, -1):
        d = (today - timedelta(days=i)).isoformat()
        day_name = (today - timedelta(days=i)).strftime("%a %b %d")
        count = day_counts.get(d, 0)
        cmds = day_commands.get(d, 0)
        bar = _mini_bar(min(count / 5, 1.0), "#7b68ee", 10) if count > 0 else "[dim]—[/]"
        table.add_row(day_name, str(count), str(cmds), bar)

    console.print(table)
