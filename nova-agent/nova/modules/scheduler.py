"""Scheduler module — reminders, timers, and scheduled tasks."""

import json
import subprocess
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

from nova.config import DEFAULT_CONFIG_DIR
from nova.utils.display import console, success, info, warning, error, section_header

TASKS_FILE = DEFAULT_CONFIG_DIR / "scheduled_tasks.json"


def _load_tasks() -> list[dict]:
    if TASKS_FILE.exists():
        try:
            return json.loads(TASKS_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return []
    return []


def _save_tasks(tasks: list[dict]):
    DEFAULT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    TASKS_FILE.write_text(json.dumps(tasks, indent=2))


def add_reminder(message: str, minutes: int):
    """Add a reminder that fires after N minutes."""
    fire_at = (datetime.now() + timedelta(minutes=minutes)).isoformat()
    tasks = _load_tasks()
    task = {
        "type": "reminder",
        "message": message,
        "fire_at": fire_at,
        "created": datetime.now().isoformat(),
        "status": "pending",
    }
    tasks.append(task)
    _save_tasks(tasks)
    success(f"Reminder set: \"{message}\" in {minutes} minutes")

    # Start background timer
    def _fire():
        time.sleep(minutes * 60)
        console.print(f"\n  [bold yellow]⏰ REMINDER:[/] {message}\n")
        # Try desktop notification
        try:
            subprocess.run(
                ["notify-send", "Nova Reminder", message],
                timeout=5, capture_output=True,
            )
        except FileNotFoundError:
            pass

    thread = threading.Thread(target=_fire, daemon=True)
    thread.start()


def add_timer(label: str, seconds: int):
    """Start a countdown timer."""
    from nova.utils.display import task_progress

    info(f"Timer: {label} ({seconds}s)")
    with task_progress("Timer") as progress:
        task = progress.add_task(label, total=seconds)
        for _ in range(seconds):
            time.sleep(1)
            progress.update(task, advance=1)

    console.print(f"\n  [bold green]⏰ Timer complete:[/] {label}\n")
    try:
        subprocess.run(
            ["notify-send", "Nova Timer", f"{label} - Time's up!"],
            timeout=5, capture_output=True,
        )
    except FileNotFoundError:
        pass


def show_tasks():
    """Show all scheduled tasks and reminders."""
    from rich.table import Table

    tasks = _load_tasks()
    if not tasks:
        info("No scheduled tasks. Use '/remind <message> <minutes>' to add one.")
        return

    section_header("Scheduled Tasks")
    table = Table(border_style="dim cyan", header_style="bold cyan")
    table.add_column("#", style="dim", justify="right", width=4)
    table.add_column("Type", style="cyan")
    table.add_column("Message", style="white")
    table.add_column("Fire At", style="yellow")
    table.add_column("Status", style="green")

    now = datetime.now()
    for i, task in enumerate(tasks, 1):
        fire_at = datetime.fromisoformat(task["fire_at"])
        status = "[green]pending[/]" if fire_at > now else "[dim]expired[/]"
        table.add_row(
            str(i), task["type"], task["message"],
            fire_at.strftime("%H:%M %b %d"), status,
        )

    console.print(table)


def clear_tasks():
    """Clear all scheduled tasks."""
    _save_tasks([])
    success("All scheduled tasks cleared")


def pomodoro(work_minutes: int = 25, break_minutes: int = 5, rounds: int = 4):
    """Run a Pomodoro timer session."""
    from nova.utils.display import task_progress

    for r in range(1, rounds + 1):
        section_header(f"Pomodoro {r}/{rounds} — Work ({work_minutes}m)")
        with task_progress(f"Working (round {r})") as progress:
            task = progress.add_task(f"Focus time", total=work_minutes * 60)
            for _ in range(work_minutes * 60):
                time.sleep(1)
                progress.update(task, advance=1)

        console.print(f"  [bold green]✓ Round {r} complete![/]")
        try:
            subprocess.run(["notify-send", "Nova Pomodoro", f"Round {r} done! Take a break."],
                           timeout=5, capture_output=True)
        except FileNotFoundError:
            pass

        if r < rounds:
            info(f"Break time: {break_minutes} minutes")
            with task_progress("Break") as progress:
                task = progress.add_task("Resting", total=break_minutes * 60)
                for _ in range(break_minutes * 60):
                    time.sleep(1)
                    progress.update(task, advance=1)
            console.print("  [bold cyan]→ Break over! Back to work.[/]\n")

    console.print("\n  [bold green]🎉 Pomodoro session complete![/]\n")
