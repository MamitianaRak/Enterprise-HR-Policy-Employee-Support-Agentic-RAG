from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Header
from app.api.chat import resolve_domain
from app.core.config import get_settings
from app.rag.registry import DEFAULT_DOMAIN, Domain
from app.services.ingestion import SUPPORTED, ingest_files

router = APIRouter(prefix="/api", tags=["ingest"])

settings = get_settings()


async def run_ingest(domain: Domain, file: UploadFile, admin_key: str):
    if admin_key != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="Invalid admin key")
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED:
        raise HTTPException(status_code=400, detail=f"Supported: {', '.join(sorted(SUPPORTED))}")
    upload_dir = Path(settings.upload_dir) / domain.name
    upload_dir.mkdir(parents=True, exist_ok=True)
    dest = upload_dir / Path(file.filename).name
    dest.write_bytes(await file.read())
    chunks, ids = ingest_files([dest], domain.name, domain.namespace)
    return {
        "message": "Document indexed",
        "domain": domain.name,
        "file": dest.name,
        "chunks": len(chunks),
        "ids_created": len(ids),
    }


@router.post("/ingest/{domain}")
async def ingest(domain: str, file: UploadFile = File(...), x_admin_key: str = Header(default="")):
    return await run_ingest(resolve_domain(domain), file, x_admin_key)


@router.post("/ingest", include_in_schema=False)
async def ingest_default(file: UploadFile = File(...), x_admin_key: str = Header(default="")):
    """Backward-compatible alias for the default domain."""
    return await run_ingest(resolve_domain(DEFAULT_DOMAIN), file, x_admin_key)
