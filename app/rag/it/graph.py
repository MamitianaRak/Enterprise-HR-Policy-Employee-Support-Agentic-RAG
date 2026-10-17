"""IT Support workflow: triage with ticket priority (P1-P4), company IT handbook and runbooks first with
per-document relevance grading, then vendor documentation on the web, self-checks and conversation memory."""
from app.core.config import get_settings
from app.rag.common.graphs import build_graded_rag_graph
from app.rag.it import prompts

settings = get_settings()


def build_graph(checkpointer=None):
    return build_graded_rag_graph(prompts, settings.it_namespace, checkpointer)
