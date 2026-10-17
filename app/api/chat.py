import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.rag.registry import DEFAULT_DOMAIN, Domain, ask, get_domain
from app.services.audit import write_audit

router = APIRouter(prefix="/api", tags=["chat"])
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=3000)


def resolve_domain(name: str) -> Domain:
    try:
        return get_domain(name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown domain: {name}")


def run_chat(domain: Domain, question: str):
    try:
        result = ask(domain, question)
        write_audit(domain.name, question, result["source_used"], result.get("trace", []))
        return {
            "domain": domain.name,
            "answer": result["answer"],
            "source_used": result["source_used"],
            "trace": result.get("trace", []),
            "citations": result.get("citations", []),
            "rewritten_query": result.get("current_query", question),
        }
    except Exception as exc:
        logger.exception("Chat request failed for domain %s", domain.name)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/chat/{domain}")
def chat(domain: str, payload: ChatRequest):
    return run_chat(resolve_domain(domain), payload.question)


@router.post("/chat", include_in_schema=False)
def chat_default(payload: ChatRequest):
    """Backward-compatible alias for the default domain."""
    return run_chat(resolve_domain(DEFAULT_DOMAIN), payload.question)
