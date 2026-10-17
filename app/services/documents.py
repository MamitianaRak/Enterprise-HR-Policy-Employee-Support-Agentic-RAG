"""Registry of indexed documents per domain, so they can be listed and deleted."""
from datetime import datetime, timezone
from app.services.db import connect


def init_documents() -> None:
    con = connect()
    con.execute(
        """CREATE TABLE IF NOT EXISTS documents (
            domain TEXT NOT NULL,
            filename TEXT NOT NULL,
            chunks INTEGER NOT NULL,
            indexed_at TEXT NOT NULL,
            PRIMARY KEY (domain, filename)
        )"""
    )
    con.commit()
    con.close()


def register_document(domain: str, filename: str, chunks: int) -> None:
    con = connect()
    con.execute(
        """INSERT INTO documents(domain, filename, chunks, indexed_at) VALUES (?, ?, ?, ?)
           ON CONFLICT(domain, filename) DO UPDATE SET chunks = excluded.chunks, indexed_at = excluded.indexed_at""",
        (domain, filename, chunks, datetime.now(timezone.utc).isoformat()),
    )
    con.commit()
    con.close()


def get_document(domain: str, filename: str) -> dict | None:
    con = connect()
    row = con.execute(
        "SELECT filename, chunks, indexed_at FROM documents WHERE domain = ? AND filename = ?", (domain, filename)
    ).fetchone()
    con.close()
    return dict(row) if row else None


def list_documents(domain: str) -> list[dict]:
    con = connect()
    rows = con.execute(
        "SELECT filename, chunks, indexed_at FROM documents WHERE domain = ? ORDER BY filename", (domain,)
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def unregister_document(domain: str, filename: str) -> None:
    con = connect()
    con.execute("DELETE FROM documents WHERE domain = ? AND filename = ?", (domain, filename))
    con.commit()
    con.close()
