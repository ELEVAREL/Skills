"""Telegram long-poll channel — drop-in transport so Nova can reply over Telegram.

Only uses stdlib. Set TELEGRAM_BOT_TOKEN in the environment.
"""

from __future__ import annotations

import json
import os
import time
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


class TelegramChannel:
    name = "telegram"

    def __init__(self, token: str | None = None, persona: str | None = None):
        self.token = token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self.persona = persona
        self.offset = 0
        self._running = False

    def _api(self, method: str, params: dict | None = None) -> dict:
        if not self.token:
            return {"ok": False, "error": "no token"}
        url = f"https://api.telegram.org/bot{self.token}/{method}"
        data = None
        if params:
            data = ("&".join(f"{k}={quote(str(v))}" for k, v in params.items())).encode("utf-8")
        req = Request(url, data=data)
        try:
            with urlopen(req, timeout=35) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (HTTPError, URLError) as e:
            return {"ok": False, "error": str(e)}

    def send(self, text: str, to: str) -> None:
        self._api("sendMessage", {"chat_id": to, "text": text[:4000]})

    def _poll(self) -> list[dict]:
        result = self._api("getUpdates", {"offset": self.offset, "timeout": 25})
        if not result.get("ok"):
            return []
        updates = result.get("result", [])
        for u in updates:
            self.offset = max(self.offset, u.get("update_id", 0) + 1)
        return updates

    def run(self) -> None:
        if not self.token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN not set")

        from nova.modules.ai_brain import AIBrain

        brain = AIBrain(persona_id=self.persona)
        self._running = True
        while self._running:
            try:
                updates = self._poll()
                for update in updates:
                    msg = update.get("message") or update.get("edited_message") or {}
                    text = msg.get("text")
                    chat = msg.get("chat") or {}
                    chat_id = chat.get("id")
                    if not text or chat_id is None:
                        continue
                    reply = brain.chat(text) or "(no response)"
                    self.send(reply, str(chat_id))
            except KeyboardInterrupt:
                self._running = False
            except Exception:
                # Keep polling even if a single round fails
                time.sleep(2)

    def stop(self) -> None:
        self._running = False
