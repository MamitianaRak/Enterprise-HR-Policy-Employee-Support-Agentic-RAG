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
    pinecone_index_name: str = "fde-hr-policy-rag"
    hr_namespace: str = Field(
        default="company-hr-kb",
        validation_alias=AliasChoices("HR_NAMESPACE", "PINECONE_NAMESPACE"),
    )
    embedding_model: str = "gemini-embedding-2-preview"
    embedding_dimension: int = 768
    gemini_model: str = "gemini-3.5-flash-lite"
    top_k: int = 4
    max_retries: int = 1
    admin_api_key: str = "change-me-in-production"
    audit_db_path: str = str(BASE_DIR / "data" / "audit.db")
    upload_dir: str = str(BASE_DIR / "uploads")
    documents_dir: str = str(BASE_DIR / "data" / "documents")
    model_config = SettingsConfigDict(env_file=str(BASE_DIR / ".env"), extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
