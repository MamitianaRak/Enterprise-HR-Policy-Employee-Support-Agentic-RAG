from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Header
from app.api.chat import resolve_domain
from app.api.errors import to_http_error
from app.core.config import get_settings
from app.rag.registry import DEFAULT_DOMAIN, Domain
from app.services.documents import list_documents
from app.services.ingestion import SUPPORTED, delete_document, ingest_file

router = APIRouter(prefix="/api", tags=["documents"])

settings = get_settings()


def require_admin(admin_key: str) -> None:
    if admin_key != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="Invalid admin key")


async def run_ingest(domain: Domain, file: UploadFile, admin_key: str):
    require_admin(admin_key)
    filename = Path(file.filename or "").name
    if Path(filename).suffix.lower() not in SUPPORTED:
        raise HTTPException(status_code=400, detail=f"Supported: {', '.join(sorted(SUPPORTED))}")
    upload_dir = Path(settings.upload_dir) / domain.name
    upload_dir.mkdir(parents=True, exist_ok=True)
    dest = upload_dir / filename
    dest.write_bytes(await file.read())
    try:
        chunks = ingest_file(dest, domain.name, domain.namespace)
    except ValueError as exc:
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise to_http_error(exc, "Indexing") from exc
    return {"message": "Document indexed", "domain": domain.name, "file": filename, "chunks": chunks}


@router.post("/ingest/{domain}")
async def ingest(domain: str, file: UploadFile = File(...), x_admin_key: str = Header(default="")):
    return await run_ingest(resolve_domain(domain), file, x_admin_key)


@router.post("/ingest", include_in_schema=False)
async def ingest_default(file: UploadFile = File(...), x_admin_key: str = Header(default="")):
    """Backward-compatible alias for the default domain."""
    return await run_ingest(resolve_domain(DEFAULT_DOMAIN), file, x_admin_key)


@router.get("/documents/{domain}")
def documents(domain: str):
    d = resolve_domain(domain)
    return {"domain": d.name, "documents": list_documents(d.name)}


@router.delete("/documents/{domain}/{filename}")
def remove_document(domain: str, filename: str, x_admin_key: str = Header(default="")):
    require_admin(x_admin_key)
    d = resolve_domain(domain)
    if Path(filename).name != filename:
        raise HTTPException(status_code=400, detail="Invalid file name")
    try:
        delete_document(d.name, filename, d.namespace)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Document not found: {filename}")
    except Exception as exc:
        raise to_http_error(exc, "Deleting document") from exc
    return {"deleted": True, "domain": d.name, "file": filename}
