from fastapi import APIRouter
from app.core.config import get_settings
from app.core.llm import gateway_chain
from app.rag.registry import public_config

router = APIRouter(prefix="/api", tags=["health"])

settings = get_settings()


@router.get("/health")
def health():
    # Model chains only, never keys: shows which providers the gateway would try, in order.
    return {
        "status": "ok",
        "service": settings.app_name,
        "models": {
            "llm": gateway_chain(settings, "answer") or "not configured",
            "llm_fast": gateway_chain(settings, "fast") or "not configured",
            "embeddings": f"pinecone:{settings.embedding_model} ({settings.embedding_dimension}d)",
        },
    }


@router.get("/domains")
def domains():
    return public_config()
