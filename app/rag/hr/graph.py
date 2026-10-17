from langgraph.graph import StateGraph, START, END
from app.core.config import get_settings
from app.rag.common import nodes
from app.rag.common.state import AgentState
from app.rag.hr import prompts

settings = get_settings()


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("route_question", nodes.router_node(prompts.ROUTER))
    graph.add_node("retrieve_kb", nodes.retrieve_node(settings.hr_namespace))
    graph.add_node("grade_kb", nodes.grade_kb_node(prompts.GRADE_KB))
    graph.add_node("search_web", nodes.search_web)
    graph.add_node("grade_web", nodes.grade_web_node(prompts.GRADE_WEB))
    graph.add_node("rewrite_query", nodes.rewrite_node(prompts.REWRITE))
    graph.add_node("generate_from_kb", nodes.generate_kb_node(prompts.GENERATE_KB))
    graph.add_node("generate_from_web", nodes.generate_web_node(prompts.GENERATE_WEB))
    graph.add_node("direct_answer", nodes.direct_node(prompts.DIRECT))
    graph.add_node("insufficient", nodes.insufficient_node(prompts.INSUFFICIENT))

    graph.add_edge(START, "route_question")
    graph.add_conditional_edges("route_question", nodes.after_router, {
        "retrieve_kb": "retrieve_kb", "direct_answer": "direct_answer"
    })
    graph.add_edge("retrieve_kb", "grade_kb")
    graph.add_conditional_edges("grade_kb", nodes.after_kb, {
        "generate_from_kb": "generate_from_kb", "search_web": "search_web"
    })
    graph.add_edge("search_web", "grade_web")
    graph.add_conditional_edges("grade_web", nodes.after_web, {
        "generate_from_web": "generate_from_web", "rewrite_query": "rewrite_query", "insufficient": "insufficient"
    })
    graph.add_edge("rewrite_query", "retrieve_kb")
    graph.add_edge("generate_from_kb", END)
    graph.add_edge("generate_from_web", END)
    graph.add_edge("direct_answer", END)
    graph.add_edge("insufficient", END)
    return graph.compile()
