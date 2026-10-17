"""Shared connection to the application SQLite database (audit, conversations, documents)."""
import sqlite3
from pathlib import Path
from app.core.config import get_settings

settings = get_settings()


def connect() -> sqlite3.Connection:
    Path(settings.audit_db_path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(settings.audit_db_path)
    con.row_factory = sqlite3.Row
    return con
