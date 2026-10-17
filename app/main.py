from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.api import chat, health, ingest, sessions
from app.core.config import get_settings, BASE_DIR
from app.core.logging import configure_logging
from app.services.audit import init_db
from app.services.conversations import init_conversations
from app.services.documents import init_documents


configure_logging()
settings = get_settings()
init_db()
init_conversations()
init_documents()


app = FastAPI(title=settings.app_name, version="1.1.0")
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(ingest.router)
app.include_router(sessions.router)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def asset_version() -> int:
    """Changes whenever a static file changes, so browsers never keep a stale CSS/JS."""
    return int(max(p.stat().st_mtime for p in (BASE_DIR / "static").rglob("*") if p.is_file()))


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request, "index.html", {"app_name": settings.app_name, "asset_version": asset_version()}
    )
