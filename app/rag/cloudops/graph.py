"""CloudOps workflow (Self-RAG): triage, private runbooks first with per-document relevance grading,
internal query rewrite, then web search, self-checks on the answer, and incident memory."""
from langgraph.graph import StateGraph, START, END
from app.core.config import get_settings
from app.rag.cloudops import prompts
from app.rag.common import nodes
from app.rag.common.state import AgentState

settings = get_settings()


def build_graph(checkpointer=None):
    graph = StateGraph(AgentState)
    graph.add_node("contextualize", nodes.contextualize_node(prompts.CONTEXTUALIZE))
    graph.add_node("triage", nodes.triage_node(prompts.TRIAGE))
    graph.add_node("retrieve_kb", nodes.retrieve_candidates_node(settings.cloudops_namespace))
    graph.add_node("grade_documents", nodes.grade_documents_node(prompts.GRADE_DOCUMENTS))
    graph.add_node("rewrite_internal", nodes.rewrite_internal_node(prompts.REWRITE_INTERNAL))
    graph.add_node("rewrite_web", nodes.rewrite_web_node(prompts.REWRITE_WEB))
    graph.add_node("search_web", nodes.search_web_docs)
    graph.add_node("generate", nodes.generate_evidence_node(prompts.GENERATE))
    graph.add_node("check_support", nodes.check_support_node(prompts.CHECK_SUPPORT))
    graph.add_node("revise_answer", nodes.revise_node(prompts.REVISE))
    graph.add_node("check_usefulness", nodes.check_usefulness_node(prompts.CHECK_USEFULNESS))
    graph.add_node("direct_answer", nodes.direct_node(prompts.DIRECT))
    graph.add_node("insufficient", nodes.insufficient_node(prompts.INSUFFICIENT))
    graph.add_node("commit_memory", nodes.commit_memory)

    graph.add_edge(START, "contextualize")
    graph.add_edge("contextualize", "triage")
    graph.add_conditional_edges("triage", nodes.after_router, {
        "retrieve_kb": "retrieve_kb", "direct_answer": "direct_answer"
    })

    # Gather evidence: private runbooks → rewrite and retry → web search.
    graph.add_edge("retrieve_kb", "grade_documents")
    graph.add_conditional_edges("grade_documents", nodes.after_grading, {
        "generate": "generate", "rewrite_internal": "rewrite_internal",
        "rewrite_web": "rewrite_web", "insufficient": "insufficient",
    })
    graph.add_edge("rewrite_internal", "retrieve_kb")
    graph.add_edge("rewrite_web", "search_web")
    graph.add_edge("search_web", "grade_documents")

    # Self-checks on the generated answer.
    graph.add_edge("generate", "check_support")
    graph.add_conditional_edges("check_support", nodes.after_support, {
        "check_usefulness": "check_usefulness", "revise_answer": "revise_answer", "insufficient": "insufficient"
    })
    graph.add_edge("revise_answer", "check_support")
    graph.add_conditional_edges("check_usefulness", nodes.after_graded_usefulness, {
        "commit_memory": "commit_memory", "rewrite_internal": "rewrite_internal",
        "rewrite_web": "rewrite_web", "insufficient": "insufficient",
    })

    graph.add_edge("direct_answer", "commit_memory")
    graph.add_edge("insufficient", "commit_memory")
    graph.add_edge("commit_memory", END)
    return graph.compile(checkpointer=checkpointer)
