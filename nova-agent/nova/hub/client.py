"""Hub client — resolves skill index, installs, uninstalls."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

HUB_DIR = Path.home() / ".nova" / "hub"
LOCAL_INDEX = HUB_DIR / "index.json"
USER_SKILLS_DIR = Path.home() / ".nova" / "skills"
DEFAULT_REMOTE = os.environ.get("NOVA_HUB_URL", "")


@dataclass
class HubEntry:
    id: str
    name: str
    description: str
    version: str
    source: str          # "git", "local", or "url"
    location: str        # git URL, local path, or download URL
    tags: list[str] = field(default_factory=list)
    author: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "HubEntry":
        return cls(
            id=d["id"],
            name=d.get("name", d["id"]),
            description=d.get("description", ""),
            version=str(d.get("version", "0.0.1")),
            source=d.get("source", "local"),
            location=d.get("location", ""),
            tags=list(d.get("tags") or []),
            author=d.get("author", ""),
        )


class HubClient:
    def __init__(self, remote_url: str = DEFAULT_REMOTE):
        self.remote_url = remote_url
        HUB_DIR.mkdir(parents=True, exist_ok=True)
        USER_SKILLS_DIR.mkdir(parents=True, exist_ok=True)

    def _seed_local_index(self) -> None:
        if LOCAL_INDEX.exists():
            return
        seed = {
            "version": 1,
            "updated": 0,
            "entries": [
                {
                    "id": "nova-web-fetch-extra",
                    "name": "web-fetch-extra",
                    "description": "Example community skill stub — placeholder for hub demos",
                    "version": "0.0.1",
                    "source": "local",
                    "location": "",
                    "tags": ["example", "placeholder"],
                    "author": "nova-community",
                }
            ],
        }
        LOCAL_INDEX.write_text(json.dumps(seed, indent=2))

    def refresh(self) -> dict:
        """Pull the latest index. Uses remote if configured, else keeps local seed."""
        if self.remote_url:
            try:
                req = Request(self.remote_url, headers={"User-Agent": "Nova-Agent-Hub/0.3"})
                with urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                LOCAL_INDEX.write_text(json.dumps(data, indent=2))
                return {"ok": True, "source": "remote", "entries": len(data.get("entries", []))}
            except (HTTPError, URLError, json.JSONDecodeError) as e:
                return {"ok": False, "error": f"remote fetch failed: {e}"}
        self._seed_local_index()
        data = json.loads(LOCAL_INDEX.read_text())
        return {"ok": True, "source": "local", "entries": len(data.get("entries", []))}

    def _load_index(self) -> list[HubEntry]:
        if not LOCAL_INDEX.exists():
            self._seed_local_index()
        try:
            data = json.loads(LOCAL_INDEX.read_text())
        except json.JSONDecodeError:
            return []
        return [HubEntry.from_dict(e) for e in data.get("entries", [])]

    def list(self) -> list[HubEntry]:
        return self._load_index()

    def search(self, query: str) -> list[HubEntry]:
        q = query.lower()
        return [
            e for e in self._load_index()
            if q in e.id.lower() or q in e.name.lower()
            or q in e.description.lower() or any(q in t.lower() for t in e.tags)
        ]

    def install(self, entry_id: str) -> dict:
        entries = {e.id: e for e in self._load_index()}
        entry = entries.get(entry_id)
        if entry is None:
            return {"ok": False, "error": f"skill {entry_id} not in index"}

        target = USER_SKILLS_DIR / entry.id
        if target.exists():
            return {"ok": False, "error": f"{entry.id} already installed at {target}"}

        try:
            if entry.source == "git":
                if not _has_git():
                    return {"ok": False, "error": "git not installed"}
                subprocess.run(
                    ["git", "clone", "--depth", "1", entry.location, str(target)],
                    check=True, timeout=120, capture_output=True, text=True,
                )
            elif entry.source == "local":
                if not entry.location:
                    # Placeholder stub — create a minimal SKILL.md so registry picks it up
                    target.mkdir(parents=True)
                    (target / "SKILL.md").write_text(
                        f"---\nname: {entry.name}\nversion: {entry.version}\n"
                        f"description: {entry.description}\ntags: {entry.tags}\n---\n\n"
                        f"Placeholder hub entry.\n"
                    )
                else:
                    shutil.copytree(entry.location, target)
            elif entry.source == "url":
                return {"ok": False, "error": "URL source not yet supported"}
            else:
                return {"ok": False, "error": f"unknown source {entry.source!r}"}
        except subprocess.CalledProcessError as e:
            return {"ok": False, "error": e.stderr or str(e)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

        # Trigger registry reload so the new skill is immediately available
        try:
            from nova.skills import get_registry
            get_registry().discover()
        except Exception:
            pass

        return {"ok": True, "installed": str(target), "id": entry.id}

    def uninstall(self, entry_id: str) -> dict:
        target = USER_SKILLS_DIR / entry_id
        if not target.exists():
            return {"ok": False, "error": f"{entry_id} not installed"}
        try:
            shutil.rmtree(target)
        except OSError as e:
            return {"ok": False, "error": str(e)}
        try:
            from nova.skills import get_registry
            get_registry().discover()
        except Exception:
            pass
        return {"ok": True, "removed": str(target)}


def _has_git() -> bool:
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True, timeout=5)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


_singleton: HubClient | None = None


def get_hub() -> HubClient:
    global _singleton
    if _singleton is None:
        _singleton = HubClient()
    return _singleton
