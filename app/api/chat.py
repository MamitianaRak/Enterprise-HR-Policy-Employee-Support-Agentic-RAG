import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.api.errors import to_http_error
from app.rag.registry import DEFAULT_DOMAIN, Domain, ask, get_domain
from app.services.audit import write_audit
from app.services.conversations import touch_conversation

router = APIRouter(prefix="/api", tags=["chat"])

THREAD_ID_PATTERN = r"^[A-Za-z0-9_-]{3,120}$"


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=3000)
    thread_id: Optional[str] = Field(default=None, pattern=THREAD_ID_PATTERN,
                                     description="Conversation id; omit to start a new conversation")


def resolve_domain(name: str) -> Domain:
    try:
        return get_domain(name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown domain: {name}")


def run_chat(domain: Domain, payload: ChatRequest):
    question = payload.question
    thread_id = payload.thread_id or uuid.uuid4().hex
    try:
        result = ask(domain, question, thread_id)
        write_audit(domain.name, question, result["source_used"], result.get("trace", []))
        touch_conversation(domain.name, thread_id, question)
        return {
            "domain": domain.name,
            "thread_id": thread_id,
            "memory_turns": len(result.get("memory", [])),
            "answer": result["answer"],
            "source_used": result["source_used"],
            "trace": result.get("trace", []),
            "citations": result.get("citations", []),
            "rewritten_query": result.get("current_query", question),
            "support_status": result.get("support_status", ""),
            "usefulness": result.get("usefulness", ""),
        }
    except Exception as exc:
        raise to_http_error(exc, f"Answering ({domain.name})") from exc


@router.post("/chat/{domain}")
def chat(domain: str, payload: ChatRequest):
    return run_chat(resolve_domain(domain), payload)


@router.post("/chat", include_in_schema=False)
def chat_default(payload: ChatRequest):
    """Backward-compatible alias for the default domain."""
    return run_chat(resolve_domain(DEFAULT_DOMAIN), payload)
