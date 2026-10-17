from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Enterprise HR Policy Agentic RAG Copilot"
    app_env: str = "development"
    google_api_key: str = ""
    tavily_api_key: str = ""
    pinecone_api_key: str = ""
    pinecone_index_name: str = "enterprise-copilot"  # one index, one namespace per domain
    hr_namespace: str = Field(
        default="company-hr-kb",
        validation_alias=AliasChoices("HR_NAMESPACE", "PINECONE_NAMESPACE"),
    )
    cloudops_namespace: str = "cloudops-runbooks"
    it_namespace: str = "it-support-kb"
    embedding_model: str = "gemini-embedding-2-preview"
    embedding_dimension: int = 768
    gemini_model: str = "gemini-3.5-flash-lite"
    llm_timeout: float = 60
    llm_max_retries: int = 2
    max_context_chars: int = 12000
    top_k: int = 4
    max_retries: int = 1
    max_support_retries: int = 1
    max_retrieval_rewrites: int = 1  # CloudOps: internal query rewrites before going to the web
    max_web_rewrites: int = 1
    admin_api_key: str = "change-me-in-production"
    # Comma-separated origins allowed to call the API from a browser, e.g. the frontend's URL
    # when it is hosted separately. Empty = same-origin only (Vite proxy, nginx, docker compose).
    cors_origins: str = ""
    memory_turns: int = 4
    audit_db_path: str = str(BASE_DIR / "data" / "audit.db")
    memory_db_path: str = str(BASE_DIR / "data" / "memory.db")
    upload_dir: str = str(BASE_DIR / "uploads")
    documents_dir: str = str(BASE_DIR / "data" / "documents")
    model_config = SettingsConfigDict(env_file=str(BASE_DIR / ".env"), extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
