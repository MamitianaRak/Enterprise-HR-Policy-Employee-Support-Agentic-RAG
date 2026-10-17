import sqlite3
from pathlib import Path
from langgraph.checkpoint.sqlite import SqliteSaver
from app.core.config import get_settings

settings = get_settings()

_checkpointer = None


def get_checkpointer() -> SqliteSaver:
    global _checkpointer
    if _checkpointer is None:
        path = Path(settings.memory_db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        _checkpointer = SqliteSaver(sqlite3.connect(str(path), check_same_thread=False))
    return _checkpointer


RECURSION_LIMIT = 20  # the longest CloudOps path (rewrites + web + revisions) exceeds LangGraph's default 25


def thread_config(domain: str, thread_id: str) -> dict:
    # Prefix with the domain so two workflows never share a conversation.
    return {"configurable": {"thread_id": f"{domain}:{thread_id}"}, "recursion_limit": RECURSION_LIMIT}
