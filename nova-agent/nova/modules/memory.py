"""Nova persistent memory — SQLite-backed cross-session recall.

Stores typed memories (user, feedback, project, reference) with keyword search.
No external vector DB; uses SQLite FTS5 when available, falls back to LIKE.
"""

from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

DB_PATH = Path.home() / ".nova" / "memory.db"

VALID_TYPES = ("user", "feedback", "project", "reference", "fact")


@dataclass
class MemoryEntry:
    id: int
    type: str
    title: str
    body: str
    tags: list[str]
    created_at: int
    updated_at: int

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "body": self.body,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _init_schema(conn: sqlite3.Connection) -> bool:
    """Create tables. Returns True if FTS5 is available."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            tags TEXT NOT NULL DEFAULT '[]',
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_updated ON memories(updated_at)")

    # Try FTS5; if it fails, fall back to LIKE queries
    fts_ok = False
    try:
        conn.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts
            USING fts5(title, body, tags, content='memories', content_rowid='id')
            """
        )
        conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
                INSERT INTO memories_fts(rowid, title, body, tags)
                VALUES (new.id, new.title, new.body, new.tags);
            END
            """
        )
        conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
                INSERT INTO memories_fts(memories_fts, rowid, title, body, tags)
                VALUES ('delete', old.id, old.title, old.body, old.tags);
            END
            """
        )
        conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
                INSERT INTO memories_fts(memories_fts, rowid, title, body, tags)
                VALUES ('delete', old.id, old.title, old.body, old.tags);
                INSERT INTO memories_fts(rowid, title, body, tags)
                VALUES (new.id, new.title, new.body, new.tags);
            END
            """
        )
        fts_ok = True
    except sqlite3.OperationalError:
        fts_ok = False

    conn.commit()
    return fts_ok


class MemoryStore:
    def __init__(self):
        self.conn = _connect()
        self.fts = _init_schema(self.conn)

    def add(self, type_: str, title: str, body: str, tags: list[str] | None = None) -> int:
        if type_ not in VALID_TYPES:
            raise ValueError(f"invalid type {type_!r}, must be one of {VALID_TYPES}")
        now = int(time.time())
        cur = self.conn.execute(
            "INSERT INTO memories(type, title, body, tags, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (type_, title, body, json.dumps(tags or []), now, now),
        )
        self.conn.commit()
        return cur.lastrowid or 0

    def update(self, memory_id: int, *, title: str | None = None, body: str | None = None,
               tags: list[str] | None = None) -> bool:
        existing = self.get(memory_id)
        if existing is None:
            return False
        new_title = title if title is not None else existing.title
        new_body = body if body is not None else existing.body
        new_tags = tags if tags is not None else existing.tags
        self.conn.execute(
            "UPDATE memories SET title=?, body=?, tags=?, updated_at=? WHERE id=?",
            (new_title, new_body, json.dumps(new_tags), int(time.time()), memory_id),
        )
        self.conn.commit()
        return True

    def delete(self, memory_id: int) -> bool:
        cur = self.conn.execute("DELETE FROM memories WHERE id=?", (memory_id,))
        self.conn.commit()
        return cur.rowcount > 0

    def get(self, memory_id: int) -> MemoryEntry | None:
        row = self.conn.execute("SELECT * FROM memories WHERE id=?", (memory_id,)).fetchone()
        return _row_to_entry(row) if row else None

    def list(self, type_: str | None = None, limit: int = 50) -> list[MemoryEntry]:
        if type_:
            rows = self.conn.execute(
                "SELECT * FROM memories WHERE type=? ORDER BY updated_at DESC LIMIT ?",
                (type_, limit),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM memories ORDER BY updated_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [_row_to_entry(r) for r in rows]

    def search(self, query: str, limit: int = 20) -> list[MemoryEntry]:
        if not query.strip():
            return []
        if self.fts:
            try:
                sanitized = _sanitize_fts(query)
                rows = self.conn.execute(
                    "SELECT m.* FROM memories m "
                    "JOIN memories_fts f ON m.id = f.rowid "
                    "WHERE memories_fts MATCH ? "
                    "ORDER BY rank LIMIT ?",
                    (sanitized, limit),
                ).fetchall()
                return [_row_to_entry(r) for r in rows]
            except sqlite3.OperationalError:
                pass
        # LIKE fallback
        like = f"%{query}%"
        rows = self.conn.execute(
            "SELECT * FROM memories "
            "WHERE title LIKE ? OR body LIKE ? OR tags LIKE ? "
            "ORDER BY updated_at DESC LIMIT ?",
            (like, like, like, limit),
        ).fetchall()
        return [_row_to_entry(r) for r in rows]

    def recent_context(self, limit: int = 6) -> str:
        """Return a compact block of the most recently updated memories for prompt injection."""
        entries = self.list(limit=limit)
        if not entries:
            return ""
        lines = ["# Memory (recent)"]
        for e in entries:
            tag_str = f" [{', '.join(e.tags)}]" if e.tags else ""
            lines.append(f"- ({e.type}){tag_str} {e.title}: {e.body[:200]}")
        return "\n".join(lines)

    def count(self) -> dict[str, int]:
        rows = self.conn.execute(
            "SELECT type, COUNT(*) AS n FROM memories GROUP BY type"
        ).fetchall()
        return {r["type"]: r["n"] for r in rows}

    def close(self) -> None:
        self.conn.close()


def _row_to_entry(row: sqlite3.Row) -> MemoryEntry:
    try:
        tags = json.loads(row["tags"]) if row["tags"] else []
    except json.JSONDecodeError:
        tags = []
    return MemoryEntry(
        id=row["id"],
        type=row["type"],
        title=row["title"],
        body=row["body"],
        tags=tags,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _sanitize_fts(query: str) -> str:
    """FTS5 match strings need bare words, no punctuation."""
    tokens = [t for t in "".join(c if c.isalnum() or c.isspace() else " " for c in query).split() if t]
    if not tokens:
        return '""'
    return " OR ".join(f'"{t}"' for t in tokens)


_singleton: MemoryStore | None = None


def get_store() -> MemoryStore:
    global _singleton
    if _singleton is None:
        _singleton = MemoryStore()
    return _singleton


# ─── Public convenience API ─────────────────────────────────────────
def remember(type_: str, title: str, body: str, tags: list[str] | None = None) -> int:
    return get_store().add(type_, title, body, tags)


def recall(query: str, limit: int = 20) -> list[dict]:
    return [e.as_dict() for e in get_store().search(query, limit)]


def forget(memory_id: int) -> bool:
    return get_store().delete(memory_id)


def list_memories(type_: str | None = None, limit: int = 50) -> list[dict]:
    return [e.as_dict() for e in get_store().list(type_, limit)]


def memory_summary() -> str:
    counts = get_store().count()
    if not counts:
        return "No memories stored yet."
    parts = [f"{k}={v}" for k, v in sorted(counts.items())]
    return f"Memories: {', '.join(parts)} (total {sum(counts.values())})"
