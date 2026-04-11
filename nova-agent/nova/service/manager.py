"""Cross-platform service manager — no admin/root required."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

SERVICE_NAME = "NovaAgent"
SERVICE_LABEL = "ai.elevare.nova"  # macOS launchd label

CONFIG_DIR = Path.home() / ".nova"
LOG_DIR = CONFIG_DIR / "logs"
ENV_FILE = CONFIG_DIR / "env"


def _python_exe() -> str:
    return sys.executable


def _service_cmd() -> list[str]:
    return [_python_exe(), "-m", "nova.cli", "gateway", "start", "--background"]


def _ensure_dirs() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def _load_env_vars() -> dict[str, str]:
    """Read ~/.nova/env into a dict so the service inherits API keys."""
    env: dict[str, str] = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()
    return env


# ─── Linux: systemd user unit ────────────────────────────────────────
class SystemdInstaller:
    unit_dir = Path.home() / ".config" / "systemd" / "user"
    unit_file = unit_dir / "nova-agent.service"

    @classmethod
    def available(cls) -> bool:
        return bool(shutil.which("systemctl"))

    @classmethod
    def install(cls) -> dict:
        _ensure_dirs()
        cls.unit_dir.mkdir(parents=True, exist_ok=True)
        env_lines = "\n".join(f"Environment={k}={v}" for k, v in _load_env_vars().items())
        unit_body = f"""[Unit]
Description=Nova Agent — AI assistant gateway
After=network.target

[Service]
Type=simple
ExecStart={' '.join(_service_cmd())}
Restart=on-failure
RestartSec=5
{env_lines}
StandardOutput=append:{LOG_DIR / 'nova.out.log'}
StandardError=append:{LOG_DIR / 'nova.err.log'}

[Install]
WantedBy=default.target
"""
        cls.unit_file.write_text(unit_body)
        try:
            subprocess.run(["systemctl", "--user", "daemon-reload"], check=True, timeout=10)
            subprocess.run(["systemctl", "--user", "enable", "nova-agent.service"],
                           check=True, timeout=10)
            subprocess.run(["systemctl", "--user", "start", "nova-agent.service"],
                           check=True, timeout=15)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            return {"ok": False, "error": str(e)}
        return {"ok": True, "method": "systemd-user", "unit": str(cls.unit_file)}

    @classmethod
    def uninstall(cls) -> dict:
        try:
            subprocess.run(["systemctl", "--user", "stop", "nova-agent.service"], timeout=10)
            subprocess.run(["systemctl", "--user", "disable", "nova-agent.service"], timeout=10)
        except subprocess.TimeoutExpired:
            pass
        if cls.unit_file.exists():
            cls.unit_file.unlink()
        subprocess.run(["systemctl", "--user", "daemon-reload"], timeout=10)
        return {"ok": True}

    @classmethod
    def status(cls) -> dict:
        if not cls.unit_file.exists():
            return {"installed": False}
        res = subprocess.run(
            ["systemctl", "--user", "is-active", "nova-agent.service"],
            capture_output=True, text=True, timeout=10,
        )
        return {"installed": True, "state": res.stdout.strip(), "unit": str(cls.unit_file)}

    @classmethod
    def start(cls) -> dict:
        res = subprocess.run(
            ["systemctl", "--user", "start", "nova-agent.service"],
            capture_output=True, text=True, timeout=15,
        )
        return {"ok": res.returncode == 0, "error": res.stderr or None}

    @classmethod
    def stop(cls) -> dict:
        res = subprocess.run(
            ["systemctl", "--user", "stop", "nova-agent.service"],
            capture_output=True, text=True, timeout=15,
        )
        return {"ok": res.returncode == 0, "error": res.stderr or None}


# ─── macOS: launchd user agent ───────────────────────────────────────
class LaunchdInstaller:
    plist_dir = Path.home() / "Library" / "LaunchAgents"
    plist_file = plist_dir / f"{SERVICE_LABEL}.plist"

    @classmethod
    def available(cls) -> bool:
        return platform.system() == "Darwin"

    @classmethod
    def install(cls) -> dict:
        _ensure_dirs()
        cls.plist_dir.mkdir(parents=True, exist_ok=True)

        env_dict_xml = "".join(
            f"<key>{k}</key><string>{_xml_escape(v)}</string>"
            for k, v in _load_env_vars().items()
        )
        cmd = _service_cmd()
        args_xml = "".join(f"<string>{_xml_escape(p)}</string>" for p in cmd)

        plist_body = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{SERVICE_LABEL}</string>
    <key>ProgramArguments</key>
    <array>{args_xml}</array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{LOG_DIR / 'nova.out.log'}</string>
    <key>StandardErrorPath</key>
    <string>{LOG_DIR / 'nova.err.log'}</string>
    <key>EnvironmentVariables</key>
    <dict>{env_dict_xml}</dict>
</dict>
</plist>
"""
        cls.plist_file.write_text(plist_body)
        try:
            subprocess.run(["launchctl", "unload", str(cls.plist_file)], timeout=10)
        except subprocess.TimeoutExpired:
            pass
        res = subprocess.run(
            ["launchctl", "load", "-w", str(cls.plist_file)],
            capture_output=True, text=True, timeout=10,
        )
        if res.returncode != 0:
            return {"ok": False, "error": res.stderr or "launchctl load failed"}
        return {"ok": True, "method": "launchd", "plist": str(cls.plist_file)}

    @classmethod
    def uninstall(cls) -> dict:
        if cls.plist_file.exists():
            subprocess.run(["launchctl", "unload", str(cls.plist_file)], timeout=10)
            cls.plist_file.unlink()
        return {"ok": True}

    @classmethod
    def status(cls) -> dict:
        if not cls.plist_file.exists():
            return {"installed": False}
        res = subprocess.run(
            ["launchctl", "list", SERVICE_LABEL],
            capture_output=True, text=True, timeout=10,
        )
        return {"installed": True, "state": "loaded" if res.returncode == 0 else "stopped",
                "plist": str(cls.plist_file)}

    @classmethod
    def start(cls) -> dict:
        res = subprocess.run(["launchctl", "start", SERVICE_LABEL], capture_output=True, text=True, timeout=10)
        return {"ok": res.returncode == 0, "error": res.stderr or None}

    @classmethod
    def stop(cls) -> dict:
        res = subprocess.run(["launchctl", "stop", SERVICE_LABEL], capture_output=True, text=True, timeout=10)
        return {"ok": res.returncode == 0, "error": res.stderr or None}


# ─── Windows: Task Scheduler ─────────────────────────────────────────
class TaskSchedulerInstaller:
    task_name = SERVICE_NAME

    @classmethod
    def available(cls) -> bool:
        return platform.system() == "Windows" and bool(shutil.which("schtasks"))

    @classmethod
    def install(cls) -> dict:
        _ensure_dirs()

        # Use a wrapper .cmd file so env vars from ~/.nova/env are loaded before launch
        wrapper = CONFIG_DIR / "run-nova.cmd"
        env_lines = "\n".join(f"set {k}={v}" for k, v in _load_env_vars().items())
        # Wrap python path in quotes; /B runs without a console window
        wrapper_body = (
            "@echo off\r\n"
            f"cd /d \"{CONFIG_DIR}\"\r\n"
            f"{env_lines}\r\n"
            f"\"{_python_exe()}\" -m nova.cli gateway start --background "
            f"> \"{LOG_DIR / 'nova.out.log'}\" 2> \"{LOG_DIR / 'nova.err.log'}\"\r\n"
        )
        wrapper.write_text(wrapper_body)

        # Register the task: run at logon, restart on failure
        cmd = [
            "schtasks", "/Create", "/F",
            "/TN", cls.task_name,
            "/TR", f'"{wrapper}"',
            "/SC", "ONLOGON",
            "/RL", "LIMITED",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if res.returncode != 0:
            return {"ok": False, "error": res.stderr or res.stdout or "schtasks failed"}

        # Fire it once now
        subprocess.run(["schtasks", "/Run", "/TN", cls.task_name],
                       capture_output=True, text=True, timeout=30)
        return {"ok": True, "method": "schtasks", "wrapper": str(wrapper)}

    @classmethod
    def uninstall(cls) -> dict:
        subprocess.run(
            ["schtasks", "/Delete", "/F", "/TN", cls.task_name],
            capture_output=True, text=True, timeout=30,
        )
        wrapper = CONFIG_DIR / "run-nova.cmd"
        if wrapper.exists():
            wrapper.unlink()
        return {"ok": True}

    @classmethod
    def status(cls) -> dict:
        res = subprocess.run(
            ["schtasks", "/Query", "/TN", cls.task_name, "/FO", "LIST"],
            capture_output=True, text=True, timeout=15,
        )
        if res.returncode != 0:
            return {"installed": False}
        state_line = next(
            (l for l in res.stdout.splitlines() if l.strip().startswith("Status:")),
            "",
        )
        return {"installed": True, "state": state_line.split(":", 1)[-1].strip() or "unknown"}

    @classmethod
    def start(cls) -> dict:
        res = subprocess.run(
            ["schtasks", "/Run", "/TN", cls.task_name],
            capture_output=True, text=True, timeout=30,
        )
        return {"ok": res.returncode == 0, "error": res.stderr or None}

    @classmethod
    def stop(cls) -> dict:
        res = subprocess.run(
            ["schtasks", "/End", "/TN", cls.task_name],
            capture_output=True, text=True, timeout=30,
        )
        return {"ok": res.returncode == 0, "error": res.stderr or None}


# ─── Dispatcher ──────────────────────────────────────────────────────
def get_platform_installer():
    sysname = platform.system()
    if sysname == "Linux" and SystemdInstaller.available():
        return SystemdInstaller
    if sysname == "Darwin" and LaunchdInstaller.available():
        return LaunchdInstaller
    if sysname == "Windows" and TaskSchedulerInstaller.available():
        return TaskSchedulerInstaller
    return None


def install_service() -> dict:
    installer = get_platform_installer()
    if installer is None:
        return {"ok": False, "error": f"no installer for {platform.system()}"}
    return installer.install()


def uninstall_service() -> dict:
    installer = get_platform_installer()
    if installer is None:
        return {"ok": False, "error": f"no installer for {platform.system()}"}
    return installer.uninstall()


def service_status() -> dict:
    installer = get_platform_installer()
    if installer is None:
        return {"installed": False, "error": f"no installer for {platform.system()}"}
    return installer.status()


def start_service() -> dict:
    installer = get_platform_installer()
    if installer is None:
        return {"ok": False, "error": f"no installer for {platform.system()}"}
    return installer.start()


def stop_service() -> dict:
    installer = get_platform_installer()
    if installer is None:
        return {"ok": False, "error": f"no installer for {platform.system()}"}
    return installer.stop()


def _xml_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )
