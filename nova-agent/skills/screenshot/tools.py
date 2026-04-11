"""screenshot skill — grab the screen and save to disk."""

from __future__ import annotations

import platform
import subprocess
import time
from pathlib import Path

TOOLS = [
    {
        "name": "take_screenshot",
        "description": "Capture the primary screen to a PNG in ~/.nova/screenshots. Returns the saved path.",
        "input_schema": {
            "type": "object",
            "properties": {
                "label": {"type": "string", "description": "Optional filename label"},
            },
        },
    },
]


def _out_dir() -> Path:
    d = Path.home() / ".nova" / "screenshots"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _filename(label: str | None) -> Path:
    ts = time.strftime("%Y%m%d-%H%M%S")
    slug = (label or "screen").replace(" ", "_")[:40]
    return _out_dir() / f"{ts}-{slug}.png"


def _mss_capture(path: Path) -> bool:
    try:
        import mss  # type: ignore
    except ImportError:
        return False
    try:
        with mss.mss() as sct:
            sct.shot(mon=-1, output=str(path))
        return path.exists()
    except Exception:
        return False


def _pillow_capture(path: Path) -> bool:
    try:
        from PIL import ImageGrab  # type: ignore
    except ImportError:
        return False
    try:
        img = ImageGrab.grab(all_screens=True)
        img.save(str(path), "PNG")
        return True
    except Exception:
        return False


def _native_capture(path: Path) -> bool:
    sysname = platform.system()
    try:
        if sysname == "Darwin":
            subprocess.run(["screencapture", "-x", str(path)], check=True, timeout=10)
            return path.exists()
        if sysname == "Linux":
            for cmd in (["gnome-screenshot", "-f", str(path)], ["scrot", str(path)]):
                try:
                    subprocess.run(cmd, check=True, timeout=10)
                    if path.exists():
                        return True
                except (FileNotFoundError, subprocess.CalledProcessError):
                    continue
            return False
        if sysname == "Windows":
            # PowerShell fallback using .NET
            ps = (
                "Add-Type -AssemblyName System.Windows.Forms,System.Drawing;"
                "$b=[System.Windows.Forms.Screen]::PrimaryScreen.Bounds;"
                "$bmp=New-Object Drawing.Bitmap $b.Width,$b.Height;"
                "$g=[Drawing.Graphics]::FromImage($bmp);"
                "$g.CopyFromScreen($b.Location,[Drawing.Point]::Empty,$b.Size);"
                f"$bmp.Save('{path.as_posix()}',[Drawing.Imaging.ImageFormat]::Png);"
            )
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps],
                check=True, timeout=15,
            )
            return path.exists()
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False
    return False


def execute(name: str, input_data: dict) -> str:
    if name != "take_screenshot":
        return f"Unknown tool: {name}"

    target = _filename(input_data.get("label"))
    for strategy in (_mss_capture, _pillow_capture, _native_capture):
        if strategy(target):
            return f"Saved: {target}"
    return "Error: no screenshot backend available (install mss or pillow, or a native tool)"
