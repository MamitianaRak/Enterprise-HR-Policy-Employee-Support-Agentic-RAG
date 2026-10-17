"""Turn provider failures into messages an employee can act on."""
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)

BUSY = ("429", "resource_exhausted", "quota", "rate limit", "too many requests")
SLOW = ("timeout", "timed out", "deadline")


def to_http_error(exc: Exception, action: str) -> HTTPException:
    logger.exception("%s failed", action)
    text = f"{type(exc).__name__}: {exc}".lower()
    if any(k in text for k in BUSY):
        return HTTPException(503, "The AI service is busy or its quota is reached. Please try again in a minute.")
    if any(k in text for k in SLOW):
        return HTTPException(504, "The AI service took too long to answer. Please try again.")
    if isinstance(exc, RuntimeError) and "missing" in text:
        return HTTPException(500, str(exc))  # configuration error, e.g. "GOOGLE_API_KEY is missing"
    return HTTPException(500, f"{action} failed. Check the server logs for details.")
