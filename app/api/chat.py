import json
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from app.api.errors import to_http_error
from app.rag.registry import DEFAULT_DOMAIN, Domain, ask, get_domain, stream
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


def finish_chat(domain: Domain, question: str, thread_id: str, result: dict) -> dict:
    """Record the turn and shape the response, for both the plain and the streaming endpoint."""
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


def run_chat(domain: Domain, payload: ChatRequest):
    thread_id = payload.thread_id or uuid.uuid4().hex
    try:
        result = ask(domain, payload.question, thread_id)
        return finish_chat(domain, payload.question, thread_id, result)
    except Exception as exc:
        raise to_http_error(exc, f"Answering ({domain.name})") from exc


def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/chat/{domain}/stream")
def chat_stream(domain: str, payload: ChatRequest):
    """Server-Sent Events: `start`, one `step` per new trace line, then `result` or `error`."""
    d = resolve_domain(domain)
    thread_id = payload.thread_id or uuid.uuid4().hex

    def events():
        yield sse("start", {"thread_id": thread_id})
        sent, final = 0, None
        try:
            for state in stream(d, payload.question, thread_id):
                trace = state.get("trace", [])
                for line in trace[sent:]:
                    yield sse("step", {"line": line})
                sent, final = len(trace), state
            yield sse("result", finish_chat(d, payload.question, thread_id, final))
        except Exception as exc:
            err = to_http_error(exc, f"Answering ({d.name})")
            yield sse("error", {"status": err.status_code, "detail": err.detail})

    return StreamingResponse(
        events(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/chat/{domain}")
def chat(domain: str, payload: ChatRequest):
    return run_chat(resolve_domain(domain), payload)


@router.post("/chat", include_in_schema=False)
def chat_default(payload: ChatRequest):
    """Backward-compatible alias for the default domain."""
    return run_chat(resolve_domain(DEFAULT_DOMAIN), payload)
