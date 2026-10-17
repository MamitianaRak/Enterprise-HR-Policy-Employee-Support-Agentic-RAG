from fastapi import APIRouter, Path, Query
from app.api.chat import THREAD_ID_PATTERN, resolve_domain
from app.rag.registry import clear_history, get_history
from app.services.conversations import delete_conversation, list_conversations

router = APIRouter(prefix="/api", tags=["sessions"])

ThreadId = Path(pattern=THREAD_ID_PATTERN)


@router.get("/sessions/{domain}")
def sessions(domain: str, limit: int = Query(default=50, ge=1, le=200)):
    d = resolve_domain(domain)
    return {"domain": d.name, "sessions": list_conversations(d.name, limit)}


@router.get("/sessions/{domain}/{thread_id}")
def session_history(domain: str, thread_id: str = ThreadId):
    d = resolve_domain(domain)
    return {"domain": d.name, "thread_id": thread_id, "turns": get_history(d, thread_id)}


@router.delete("/sessions/{domain}/{thread_id}")
def delete_session(domain: str, thread_id: str = ThreadId):
    d = resolve_domain(domain)
    clear_history(d, thread_id)
    delete_conversation(d.name, thread_id)
    return {"deleted": True, "domain": d.name, "thread_id": thread_id}
