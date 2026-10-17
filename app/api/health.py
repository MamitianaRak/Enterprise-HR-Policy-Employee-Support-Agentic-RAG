from fastapi import APIRouter
from app.core.config import get_settings
from app.rag.registry import DOMAINS, DEFAULT_DOMAIN

router = APIRouter(prefix="/api", tags=["health"])

settings = get_settings()


@router.get("/health")
def health():
    return {"status": "ok", "service": settings.app_name}


@router.get("/domains")
def domains():
    return {
        "default": DEFAULT_DOMAIN,
        "domains": [{"name": d.name, "label": d.label} for d in DOMAINS.values()],
    }
