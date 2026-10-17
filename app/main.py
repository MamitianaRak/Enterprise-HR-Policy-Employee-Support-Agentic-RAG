from fastapi import FastAPI
from app.api import chat, health, ingest, sessions
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.services.audit import init_db
from app.services.conversations import init_conversations
from app.services.documents import init_documents


configure_logging()
settings = get_settings()
init_db()
init_conversations()
init_documents()


# API only: the web UI is the React app in frontend/ (Vite in dev, nginx or a static host in prod).
app = FastAPI(title=settings.app_name, version="2.0.0")
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(ingest.router)
app.include_router(sessions.router)


@app.get("/", include_in_schema=False)
def root():
    return {"service": settings.app_name, "docs": "/docs", "health": "/api/health"}
