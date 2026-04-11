"""cloudflared wrapper — download + run a quick tunnel, capture the public URL."""

from __future__ import annotations

import json
import os
import platform
import re
import shutil
import signal
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

STATE_FILE = Path.home() / ".nova" / "tunnel.json"
BIN_DIR = Path.home() / ".nova" / "bin"

URL_PATTERN = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")

# Official GitHub release download URLs
DOWNLOAD_URLS = {
    ("Windows", "AMD64"): "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe",
    ("Windows", "x86_64"): "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe",
    ("Linux", "x86_64"): "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64",
    ("Linux", "aarch64"): "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64",
    ("Darwin", "x86_64"): "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64.tgz",
    ("Darwin", "arm64"): "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64.tgz",
}


class CloudflareTunnel:
    def __init__(self):
        self.binary: Path | None = self._find_binary()
        self.process: subprocess.Popen | None = None
        self.public_url: str | None = None

    # ─── Discovery ──────────────────────────────────────────────
    def _find_binary(self) -> Path | None:
        # 1. PATH
        found = shutil.which("cloudflared") or shutil.which("cloudflared.exe")
        if found:
            return Path(found)
        # 2. ~/.nova/bin
        for name in ("cloudflared", "cloudflared.exe"):
            candidate = BIN_DIR / name
            if candidate.exists():
                return candidate
        return None

    def is_installed(self) -> bool:
        return self.binary is not None

    # ─── Installer ──────────────────────────────────────────────
    def install(self) -> dict:
        sysname = platform.system()
        machine = platform.machine() or "x86_64"
        url = DOWNLOAD_URLS.get((sysname, machine))
        if url is None:
            # Fall back to generic amd64 for weird Linux arches
            url = DOWNLOAD_URLS.get((sysname, "x86_64"))
        if url is None:
            return {"ok": False, "error": f"no prebuilt cloudflared for {sysname}/{machine}"}

        BIN_DIR.mkdir(parents=True, exist_ok=True)
        target_name = "cloudflared.exe" if sysname == "Windows" else "cloudflared"
        target = BIN_DIR / target_name

        try:
            # Download
            tmp = Path(tempfile.mkdtemp()) / "download.bin"
            req = urllib.request.Request(url, headers={"User-Agent": "Nova-Agent/0.3"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                tmp.write_bytes(resp.read())

            # Handle .tgz on macOS
            if url.endswith(".tgz"):
                import tarfile
                with tarfile.open(tmp, "r:gz") as tf:
                    for member in tf.getmembers():
                        if member.name.endswith("cloudflared"):
                            with tf.extractfile(member) as src, open(target, "wb") as dst:
                                if src is not None:
                                    dst.write(src.read())
                            break
            else:
                shutil.copy(tmp, target)

            if sysname != "Windows":
                target.chmod(0o755)

            self.binary = target
            return {"ok": True, "path": str(target)}

        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ─── Start/stop ─────────────────────────────────────────────
    def start(self, local_port: int = 7878, timeout: float = 25.0) -> dict:
        """Launch a quick tunnel and return the public URL once it appears."""
        if self.binary is None and not self.install().get("ok"):
            return {"ok": False, "error": "cloudflared not installed"}

        log_file = Path.home() / ".nova" / "logs" / "cloudflared.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        log_fd = open(log_file, "a", buffering=1)

        cmd = [
            str(self.binary),
            "tunnel",
            "--url", f"http://127.0.0.1:{local_port}",
            "--no-autoupdate",
        ]

        self.process = subprocess.Popen(
            cmd,
            stdout=log_fd,
            stderr=subprocess.STDOUT,
            text=True,
        )

        # Poll the log for the public URL
        start = time.time()
        url: str | None = None
        while time.time() - start < timeout:
            if self.process.poll() is not None:
                return {"ok": False, "error": f"cloudflared exited early (see {log_file})"}
            try:
                content = log_file.read_text(errors="replace")
                match = URL_PATTERN.search(content)
                if match:
                    url = match.group(0)
                    break
            except OSError:
                pass
            time.sleep(0.4)

        if url is None:
            self.stop()
            return {"ok": False, "error": f"timed out waiting for tunnel URL (see {log_file})"}

        self.public_url = url
        self._save_state({"url": url, "pid": self.process.pid, "port": local_port})
        return {"ok": True, "url": url, "pid": self.process.pid}

    def stop(self) -> dict:
        state = self._load_state()
        pid = state.get("pid")
        if pid:
            try:
                if platform.system() == "Windows":
                    subprocess.run(["taskkill", "/F", "/PID", str(pid)],
                                   capture_output=True, timeout=10)
                else:
                    os.kill(int(pid), signal.SIGTERM)
            except (ProcessLookupError, PermissionError, subprocess.TimeoutExpired):
                pass
        self._clear_state()
        return {"ok": True}

    def status(self) -> dict:
        state = self._load_state()
        if not state:
            return {"running": False}
        pid = state.get("pid")
        if not pid:
            return {"running": False}
        # Best-effort liveness check
        alive = False
        try:
            if platform.system() == "Windows":
                res = subprocess.run(
                    ["tasklist", "/FI", f"PID eq {pid}"],
                    capture_output=True, text=True, timeout=10,
                )
                alive = str(pid) in res.stdout
            else:
                os.kill(int(pid), 0)
                alive = True
        except (ProcessLookupError, PermissionError, subprocess.TimeoutExpired):
            alive = False
        return {"running": alive, "url": state.get("url"), "pid": pid}

    # ─── State persistence ─────────────────────────────────────
    def _save_state(self, state: dict) -> None:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(state, indent=2))

    def _load_state(self) -> dict:
        if STATE_FILE.exists():
            try:
                return json.loads(STATE_FILE.read_text())
            except json.JSONDecodeError:
                return {}
        return {}

    def _clear_state(self) -> None:
        if STATE_FILE.exists():
            STATE_FILE.unlink()
