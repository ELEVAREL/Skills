"""web-fetch skill — safe HTTP GET with plaintext extraction."""

from __future__ import annotations

import ipaddress
import re
import socket
from html.parser import HTMLParser
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

TOOLS = [
    {
        "name": "http_get",
        "description": "Fetch a URL and return the first 12k characters of raw body. HTTPS preferred.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "max_bytes": {"type": "integer", "default": 200000},
            },
            "required": ["url"],
        },
    },
    {
        "name": "web_read",
        "description": "Fetch a URL, strip HTML, and return readable plaintext (first 12k chars).",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
            },
            "required": ["url"],
        },
    },
]


class _TextExtractor(HTMLParser):
    _SKIP_TAGS = {"script", "style", "noscript", "svg", "head"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.chunks: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self._SKIP_TAGS:
            self._skip_depth += 1
        elif tag in ("br", "p", "div", "li", "tr", "h1", "h2", "h3", "h4"):
            self.chunks.append("\n")

    def handle_endtag(self, tag):
        if tag in self._SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data):
        if self._skip_depth:
            return
        if data.strip():
            self.chunks.append(data)

    def text(self) -> str:
        return re.sub(r"\n{3,}", "\n\n", "".join(self.chunks).strip())


def _validate_url(url: str) -> str | None:
    """Return the URL if safe, else an error string."""
    try:
        parsed = urlparse(url)
    except ValueError:
        return None
    if parsed.scheme not in ("http", "https"):
        return None
    if not parsed.hostname:
        return None
    try:
        ip = socket.gethostbyname(parsed.hostname)
        addr = ipaddress.ip_address(ip)
        if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_multicast:
            return None
    except (socket.gaierror, ValueError):
        # Let urlopen surface the real error
        pass
    return url


def _fetch(url: str, max_bytes: int) -> tuple[int, str, bytes]:
    req = Request(url, headers={"User-Agent": "Nova-Agent/0.3 (+nova-cli)"})
    with urlopen(req, timeout=15) as resp:
        body = resp.read(max_bytes)
        status = resp.status
        ctype = resp.headers.get("Content-Type", "")
    return status, ctype, body


def execute(name: str, input_data: dict) -> str:
    url = input_data.get("url", "")
    if not _validate_url(url):
        return f"Refused: unsafe or invalid URL: {url!r}"

    try:
        if name == "http_get":
            max_bytes = int(input_data.get("max_bytes", 200000))
            status, ctype, body = _fetch(url, max_bytes)
            text = body.decode("utf-8", errors="replace")[:12000]
            return f"HTTP {status} ({ctype})\n\n{text}"

        if name == "web_read":
            status, ctype, body = _fetch(url, 500000)
            if "html" not in ctype.lower() and "xml" not in ctype.lower():
                return f"HTTP {status} ({ctype})\n\n{body.decode('utf-8', errors='replace')[:12000]}"
            parser = _TextExtractor()
            parser.feed(body.decode("utf-8", errors="replace"))
            return f"HTTP {status} — {url}\n\n{parser.text()[:12000]}"

    except HTTPError as e:
        return f"HTTP error {e.code}: {e.reason}"
    except URLError as e:
        return f"Fetch failed: {e.reason}"
    except Exception as e:
        return f"Error: {e}"

    return f"Unknown tool: {name}"
