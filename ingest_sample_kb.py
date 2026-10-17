import argparse
from pathlib import Path
from app.core.config import get_settings
from app.rag.registry import DOMAINS, DEFAULT_DOMAIN
from app.services.ingestion import SUPPORTED, ingest_files


settings = get_settings()

parser = argparse.ArgumentParser(description="Index the sample documents of a domain into Pinecone.")
parser.add_argument("--domain", default=DEFAULT_DOMAIN, choices=sorted(DOMAINS))
args = parser.parse_args()

domain = DOMAINS[args.domain]
folder = Path(settings.documents_dir) / domain.name
files = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED]
if not files:
    raise SystemExit(f"No supported documents found in {folder}")

chunks, ids = ingest_files(files, domain.name, domain.namespace)
print(f"[{domain.name}] Indexed {len(files)} files -> {len(chunks)} chunks -> {len(ids)} Pinecone vectors (namespace: {domain.namespace})")
