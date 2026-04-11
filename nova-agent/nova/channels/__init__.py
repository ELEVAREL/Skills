"""Nova Channels — message transports that route user input into Nova's brain.

A Channel is anything that can:
  1. Receive messages from a user (terminal, HTTP, Telegram, Slack, ...)
  2. Call the brain (directly or via the gateway)
  3. Deliver the response back

This package ships three reference channels:
  - terminal: the default interactive shell (lives in nova/cli.py)
  - http_client: a thin client that hits the Nova gateway
  - telegram: long-poll bot (needs TELEGRAM_BOT_TOKEN env var)
"""

from nova.channels.base import Channel, ChannelMessage
from nova.channels.http_client import HttpClientChannel
from nova.channels.telegram import TelegramChannel

__all__ = ["Channel", "ChannelMessage", "HttpClientChannel", "TelegramChannel"]
