"""Reusable LangGraph nodes. Each factory takes the domain-specific prompt or namespace
and returns a node function, so every domain can assemble its own graph."""
from pathlib import Path
from typing import Literal
from langchain_tavily import TavilySearch
from app.core.config import get_settings
from app.core.llm import llm, text_of
from app.rag.common.state import AgentState, RouteDecision, EvidenceGrade
from app.rag.common.vectorstore import get_retriever

settings = get_settings()

_web_search = None


def web_search_tool():
    global _web_search
    if _web_search is None:
        if not settings.tavily_api_key:
            raise RuntimeError("TAVILY_API_KEY is missing")
        _web_search = TavilySearch(
            tavily_api_key=settings.tavily_api_key,
            max_results=5,
            topic="general",
            include_answer=True,
            include_raw_content=False,
        )
    return _web_search


def add_trace(state: AgentState, message: str):
    return [*state.get("trace", []), message]


def source_name(doc) -> str:
    return doc.metadata.get("filename") or Path(doc.metadata.get("source", "unknown")).name


def format_docs(docs) -> str:
    return "\n\n".join(f"[Source: {source_name(d)}]\n{d.page_content}" for d in docs)


# ---- Nodes ----

def router_node(prompt: str):
    def route_question(state: AgentState):
        router = llm().with_structured_output(RouteDecision, method="json_mode")
        decision = router.invoke(prompt.format(question=state["question"]))
        return {"source_used": decision.route, "trace": add_trace(state, f"Router → {decision.route.upper()}")}
    return route_question


def retrieve_node(namespace: str):
    def retrieve_kb(state: AgentState):
        docs = get_retriever(namespace).invoke(state["current_query"])
        return {"kb_docs": docs, "trace": add_trace(state, f"Private KB retrieval → {len(docs)} chunks")}
    return retrieve_kb


def grade_kb_node(prompt: str):
    def grade_kb(state: AgentState):
        grader = llm().with_structured_output(EvidenceGrade, method="json_mode")
        grade = grader.invoke(prompt.format(question=state["question"], context=format_docs(state["kb_docs"])))
        return {"kb_grade": grade.grade, "trace": add_trace(state, f"KB evidence grade → {grade.grade.upper()}")}
    return grade_kb


def search_web(state: AgentState):
    result = web_search_tool().invoke({"query": state["current_query"]})
    lines, citations = [], []
    if isinstance(result, dict):
        if result.get("answer"):
            lines.append("Search answer: " + result["answer"])
        for item in result.get("results", []):
            title, url, content = item.get("title", ""), item.get("url", ""), item.get("content", "")
            lines.append(f"Title: {title}\nURL: {url}\nContent: {content}")
            citations.append({"title": title or url, "url": url, "type": "web"})
    else:
        lines.append(str(result))
    return {
        "web_results": "\n\n".join(lines),
        "citations": citations,
        "source_used": "web",
        "trace": add_trace(state, "Web fallback → Tavily search"),
    }


def grade_web_node(prompt: str):
    def grade_web(state: AgentState):
        grader = llm().with_structured_output(EvidenceGrade, method="json_mode")
        grade = grader.invoke(prompt.format(question=state["question"], evidence=state["web_results"]))
        return {"web_grade": grade.grade, "trace": add_trace(state, f"Web evidence grade → {grade.grade.upper()}")}
    return grade_web


def rewrite_node(prompt: str):
    def rewrite_query(state: AgentState):
        rewritten = text_of(llm().invoke(prompt.format(question=state["question"])))
        return {
            "current_query": rewritten,
            "retry_count": state["retry_count"] + 1,
            "trace": add_trace(state, f"Query rewrite → {rewritten}"),
        }
    return rewrite_query


def generate_kb_node(prompt: str):
    def generate_from_kb(state: AgentState):
        answer = text_of(llm().invoke(prompt.format(question=state["question"], context=format_docs(state["kb_docs"]))))
        citations, seen = [], set()
        for d in state["kb_docs"]:
            name = source_name(d)
            if name not in seen:
                seen.add(name)
                citations.append({"title": name, "url": "", "type": "private_kb"})
        return {"answer": answer, "source_used": "private_kb", "citations": citations, "trace": add_trace(state, "Answer generation → PRIVATE KB")}
    return generate_from_kb


def generate_web_node(prompt: str):
    def generate_from_web(state: AgentState):
        answer = text_of(llm().invoke(prompt.format(question=state["question"], evidence=state["web_results"])))
        return {"answer": answer, "source_used": "web_search", "trace": add_trace(state, "Answer generation → WEB SEARCH")}
    return generate_from_web


def direct_node(prompt: str):
    def direct_answer(state: AgentState):
        answer = text_of(llm().invoke(prompt.format(question=state["question"])))
        return {"answer": answer, "source_used": "direct", "trace": add_trace(state, "Direct response → no retrieval")}
    return direct_answer


def insufficient_node(message: str):
    def insufficient(state: AgentState):
        return {
            "answer": message,
            "source_used": "insufficient_evidence",
            "trace": add_trace(state, "Stopped → insufficient reliable evidence"),
        }
    return insufficient


# ---- Edge conditions ----

def after_router(state: AgentState) -> Literal["retrieve_kb", "direct_answer"]:
    return "retrieve_kb" if state["source_used"] == "kb" else "direct_answer"


def after_kb(state: AgentState) -> Literal["generate_from_kb", "search_web"]:
    return "generate_from_kb" if state["kb_grade"] == "good" else "search_web"


def after_web(state: AgentState) -> Literal["generate_from_web", "rewrite_query", "insufficient"]:
    if state["web_grade"] == "good":
        return "generate_from_web"
    if state["retry_count"] < settings.max_retries:
        return "rewrite_query"
    return "insufficient"
