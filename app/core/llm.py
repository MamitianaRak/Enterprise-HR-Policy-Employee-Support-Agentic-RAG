from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import get_settings

settings = get_settings()

_llm = None


def llm():
    global _llm
    if _llm is None:
        if not settings.google_api_key:
            raise RuntimeError("GOOGLE_API_KEY is missing")
        _llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            temperature=0,
            google_api_key=settings.google_api_key,
        )
    return _llm


def text_of(message) -> str:
    """Chat models may return content as a list of blocks; always return plain text."""
    content = getattr(message, "content", message)
    if isinstance(content, list):
        content = "".join(
            p if isinstance(p, str) else p.get("text", "") for p in content
        )
    return str(content).strip()
