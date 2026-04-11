"""Nova Gateway HTTP server — zero-dependency stdlib implementation."""

from __future__ import annotations

import json
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable

TOKEN_FILE = Path.home() / ".nova" / "gateway.token"


def _ensure_token() -> str:
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip()
    token = secrets.token_urlsafe(32)
    TOKEN_FILE.write_text(token)
    try:
        TOKEN_FILE.chmod(0o600)
    except OSError:
        pass
    return token


class _Handler(BaseHTTPRequestHandler):
    server_version = "NovaGateway/0.3"
    # Will be injected
    routes: dict[tuple[str, str], Callable] = {}
    token: str = ""

    def log_message(self, format, *args):  # noqa: A002 — silence default noise
        return

    def _json(self, status: int, payload: dict | list) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    PUBLIC_PATHS = ("/healthz", "/v1/telegram")

    def _authenticated(self) -> bool:
        path = self.path.split("?", 1)[0]
        if path in self.PUBLIC_PATHS:
            return True
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return False
        return secrets.compare_digest(auth[7:].strip(), self.token)

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}

    def do_OPTIONS(self):  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.end_headers()

    def do_GET(self):  # noqa: N802
        self._dispatch("GET")

    def do_POST(self):  # noqa: N802
        self._dispatch("POST")

    def _dispatch(self, method: str) -> None:
        if not self._authenticated():
            self._json(401, {"error": "unauthorized"})
            return
        path = self.path.split("?", 1)[0]
        handler = self.routes.get((method, path))
        if handler is None:
            self._json(404, {"error": "not found", "path": path})
            return
        try:
            body = self._read_body() if method == "POST" else {}
            result = handler(body)
            self._json(200, result)
        except Exception as e:
            self._json(500, {"error": str(e)})


class GatewayServer:
    """Wraps the ThreadingHTTPServer and exposes programmatic start/stop."""

    def __init__(self, host: str = "127.0.0.1", port: int = 7878):
        self.host = host
        self.port = port
        self.token = _ensure_token()
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self.routes: dict[tuple[str, str], Callable] = {}
        self._register_default_routes()

    def _register_default_routes(self) -> None:
        from nova.personas import get_persona_registry
        from nova.skills import get_registry as get_skill_registry
        from nova.modules.memory import get_store

        def healthz(_body):
            return {"status": "ok", "service": "nova-gateway"}

        def list_personas(_body):
            reg = get_persona_registry()
            return {
                "active": reg.active_id or "nova-default",
                "personas": [
                    {"id": p.id, "name": p.name, "description": p.description,
                     "tags": p.tags, "skills": p.skills}
                    for p in reg.list_all()
                ],
            }

        def set_active_persona(body):
            reg = get_persona_registry()
            p = reg.activate(body.get("id", ""))
            if p is None:
                return {"ok": False, "error": "persona not found"}
            return {"ok": True, "active": p.id, "greeting": p.greeting}

        def list_skills(_body):
            reg = get_skill_registry()
            return {
                "skills": [
                    {"id": s.id, "name": s.name, "version": s.version,
                     "description": s.description, "tools": s.tool_names(),
                     "enabled": s.enabled, "tags": s.tags}
                    for s in reg.skills.values()
                ],
            }

        def toggle_skill(body):
            reg = get_skill_registry()
            skill_id = body.get("id", "")
            enabled = bool(body.get("enabled", True))
            ok = reg.enable(skill_id) if enabled else reg.disable(skill_id)
            return {"ok": ok, "id": skill_id, "enabled": enabled}

        def chat(body):
            from nova.modules.ai_brain import AIBrain
            message = body.get("message", "")
            if not message:
                return {"error": "message required"}
            persona_id = body.get("persona")
            brain = AIBrain(persona_id=persona_id)
            response = brain.chat(message)
            return {
                "persona": persona_id or "nova-default",
                "response": response or "",
            }

        def list_memory(_body):
            return {"memories": [e.as_dict() for e in get_store().list(limit=100)]}

        def telegram_webhook(body):
            """Handle an incoming Telegram Update and reply in place."""
            import os
            token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
            if not token:
                return {"ok": False, "error": "TELEGRAM_BOT_TOKEN not set"}

            msg = body.get("message") or body.get("edited_message") or {}
            text = msg.get("text")
            chat = msg.get("chat") or {}
            chat_id = chat.get("id")
            if not text or chat_id is None:
                return {"ok": True, "ignored": True}

            # Route through the brain using whichever persona is active
            from nova.modules.ai_brain import AIBrain
            from nova.personas import get_persona_registry
            active = get_persona_registry().active()
            brain = AIBrain(persona_id=active.id if active else None)
            reply = brain.chat(text) or "(no response)"

            # Send reply back via Telegram API
            from nova.channels.telegram import TelegramChannel
            TelegramChannel(token=token).send(reply, str(chat_id))
            return {"ok": True}

        def add_memory(body):
            type_ = body.get("type", "fact")
            title = body.get("title", "")
            content = body.get("body", "")
            tags = body.get("tags") or []
            if not title or not content:
                return {"error": "title and body required"}
            mid = get_store().add(type_, title, content, tags)
            return {"ok": True, "id": mid}

        self.routes = {
            ("GET", "/healthz"): healthz,
            ("GET", "/v1/personas"): list_personas,
            ("POST", "/v1/personas/active"): set_active_persona,
            ("GET", "/v1/skills"): list_skills,
            ("POST", "/v1/skills/toggle"): toggle_skill,
            ("POST", "/v1/chat"): chat,
            ("GET", "/v1/memory"): list_memory,
            ("POST", "/v1/memory"): add_memory,
            ("POST", "/v1/telegram"): telegram_webhook,
        }

    def start(self) -> None:
        if self._server is not None:
            return

        handler_cls = type(
            "BoundHandler",
            (_Handler,),
            {"routes": self.routes, "token": self.token},
        )
        self._server = ThreadingHTTPServer((self.host, self.port), handler_cls)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._server is None:
            return
        self._server.shutdown()
        self._server.server_close()
        self._server = None
        self._thread = None

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"


_singleton: GatewayServer | None = None


def start_gateway(host: str = "127.0.0.1", port: int = 7878) -> GatewayServer:
    global _singleton
    if _singleton is None:
        _singleton = GatewayServer(host=host, port=port)
    _singleton.start()
    return _singleton


def stop_gateway() -> None:
    global _singleton
    if _singleton is not None:
        _singleton.stop()
        _singleton = None
