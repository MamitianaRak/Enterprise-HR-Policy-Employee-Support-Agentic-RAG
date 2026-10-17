"""CloudOps workflow (Self-RAG): triage with incident severity, private runbooks first with
per-document relevance grading, internal query rewrite, then web search, self-checks, incident memory."""
from app.core.config import get_settings
from app.rag.cloudops import prompts
from app.rag.common.graphs import build_graded_rag_graph

settings = get_settings()


def build_graph(checkpointer=None):
    return build_graded_rag_graph(prompts, settings.cloudops_namespace, checkpointer)
