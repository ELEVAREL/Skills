"""HTTP client channel — talks to a running Nova gateway via REST."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

TOKEN_FILE = Path.home() / ".nova" / "gateway.token"


class HttpClientChannel:
    name = "http_client"

    def __init__(self, base_url: str = "http://127.0.0.1:7878", token: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.token = token or self._load_token()

    def _load_token(self) -> str:
        if TOKEN_FILE.exists():
            return TOKEN_FILE.read_text().strip()
        return ""

    def _request(self, method: str, path: str, body: dict | None = None) -> dict:
        url = f"{self.base_url}{path}"
        data = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        req = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(req, timeout=60) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except HTTPError as e:
            try:
                return json.loads(e.read().decode("utf-8"))
            except Exception:
                return {"error": f"HTTP {e.code}: {e.reason}"}
        except URLError as e:
            return {"error": f"connection failed: {e.reason}"}

    def chat(self, message: str, persona: str | None = None) -> dict:
        payload: dict = {"message": message}
        if persona:
            payload["persona"] = persona
        return self._request("POST", "/v1/chat", payload)

    def list_personas(self) -> dict:
        return self._request("GET", "/v1/personas")

    def activate_persona(self, persona_id: str) -> dict:
        return self._request("POST", "/v1/personas/active", {"id": persona_id})

    def list_skills(self) -> dict:
        return self._request("GET", "/v1/skills")

    def toggle_skill(self, skill_id: str, enabled: bool) -> dict:
        return self._request("POST", "/v1/skills/toggle", {"id": skill_id, "enabled": enabled})

    def health(self) -> dict:
        return self._request("GET", "/healthz")

    def send(self, text: str, to: str) -> None:
        # This channel is a client, not a receiver; send is a no-op echo.
        pass

    def run(self) -> None:
        pass
