from fastapi import APIRouter
from app.core.config import get_settings
from app.rag.registry import public_config

router = APIRouter(prefix="/api", tags=["health"])

settings = get_settings()


@router.get("/health")
def health():
    return {"status": "ok", "service": settings.app_name}


@router.get("/domains")
def domains():
    return public_config()
