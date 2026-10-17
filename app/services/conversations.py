"""Index of conversations per domain (title, turns, dates). The messages themselves
live in the LangGraph checkpointer; this table only makes them listable."""
from datetime import datetime, timezone
from app.services.db import connect

TITLE_LENGTH = 80


def init_conversations() -> None:
    con = connect()
    con.execute(
        """CREATE TABLE IF NOT EXISTS conversations (
            domain TEXT NOT NULL,
            thread_id TEXT NOT NULL,
            title TEXT NOT NULL,
            turns INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (domain, thread_id)
        )"""
    )
    con.commit()
    con.close()


def touch_conversation(domain: str, thread_id: str, question: str) -> None:
    """Create the conversation on its first question, then bump turns and updated_at."""
    now = datetime.now(timezone.utc).isoformat()
    title = question.strip().replace("\n", " ")[:TITLE_LENGTH]
    con = connect()
    con.execute(
        """INSERT INTO conversations(domain, thread_id, title, turns, created_at, updated_at)
           VALUES (?, ?, ?, 1, ?, ?)
           ON CONFLICT(domain, thread_id) DO UPDATE SET turns = turns + 1, updated_at = excluded.updated_at""",
        (domain, thread_id, title, now, now),
    )
    con.commit()
    con.close()


def list_conversations(domain: str, limit: int = 50) -> list[dict]:
    con = connect()
    rows = con.execute(
        "SELECT thread_id, title, turns, created_at, updated_at FROM conversations "
        "WHERE domain = ? ORDER BY updated_at DESC LIMIT ?",
        (domain, limit),
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def delete_conversation(domain: str, thread_id: str) -> None:
    con = connect()
    con.execute("DELETE FROM conversations WHERE domain = ? AND thread_id = ?", (domain, thread_id))
    con.commit()
    con.close()
