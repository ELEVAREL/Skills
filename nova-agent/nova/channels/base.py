"""Channel base class and message type."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class ChannelMessage:
    channel: str
    sender: str
    text: str
    reply_to: str | None = None
    metadata: dict = field(default_factory=dict)


class Channel(Protocol):
    """Minimal channel protocol. Implementations just need send() and run()."""

    name: str

    def send(self, text: str, to: str) -> None: ...
    def run(self) -> None: ...
