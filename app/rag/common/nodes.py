"""Reusable LangGraph nodes. Each factory takes the domain-specific prompt or namespace
and returns a node function, so every domain can assemble its own graph."""
import json
import logging
from pathlib import Path
from typing import Literal
from langchain_core.exceptions import OutputParserException
from langchain_tavily import TavilySearch
from pydantic import ValidationError
from app.core.config import get_settings
from app.core.llm import llm, text_of
from langchain_core.documents import Document
from app.rag.common.state import (
    AgentState, RouteDecision, EvidenceGrade, QueryRewrite, SupportDecision, UsefulnessDecision,
    RelevantDocuments, Triage,
)
from app.rag.common.vectorstore import get_retriever

logger = logging.getLogger(__name__)
settings = get_settings()

EXCERPT_LENGTH = 220

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


# ---- Helpers ----

def add_trace(state: AgentState, message: str):
    return [*state.get("trace", []), message]


def structured(schema, prompt: str, fallback):
    """Ask for structured output. Returns (result, used_fallback). Falls back only when the
    model returns malformed JSON; API errors (quota, timeout) still propagate."""
    try:
        return llm().with_structured_output(schema, method="json_mode").invoke(prompt), False
    except (OutputParserException, ValidationError, json.JSONDecodeError) as exc:
        logger.warning("Malformed %s output, using fallback %r: %s", schema.__name__, fallback, exc)
        return fallback, True


def fallback_note(used: bool) -> str:
    return " (fallback)" if used else ""


def truncate(text: str, limit: int | None = None) -> str:
    limit = limit or settings.max_context_chars
    return text if len(text) <= limit else text[:limit] + "\n[...truncated]"


def is_web(doc) -> bool:
    return doc.metadata.get("source_type") == "web"


def source_name(doc) -> str:
    if is_web(doc):
        return doc.metadata.get("title") or doc.metadata.get("url", "web result")
    return doc.metadata.get("filename") or Path(doc.metadata.get("source", "unknown")).name


def page_of(doc) -> int | None:
    """1-based page number for PDF chunks (loaders store it 0-based)."""
    page = doc.metadata.get("page")
    return int(page) + 1 if isinstance(page, (int, float)) else None


def excerpt(text: str, length: int = EXCERPT_LENGTH) -> str:
    text = " ".join(text.split())
    return text if len(text) <= length else text[:length].rsplit(" ", 1)[0] + "…"


def format_docs(docs) -> str:
    blocks = []
    for d in docs:
        if is_web(d):
            head = f"[Web: {source_name(d)} | {d.metadata.get('url', '')}]"
        else:
            page = page_of(d)
            head = f"[Source: {source_name(d)}{f' | page {page}' if page else ''}]"
        blocks.append(f"{head}\n{d.page_content}")
    return truncate("\n\n".join(blocks))


def doc_citations(docs) -> list[dict]:
    """One citation per (document, page) for internal chunks, per URL for web results."""
    citations, seen = [], set()
    for d in docs:
        web = is_web(d)
        key = ("web", d.metadata.get("url", "")) if web else (source_name(d), page_of(d))
        if key in seen:
            continue
        seen.add(key)
        citations.append({
            "title": source_name(d),
            "page": None if web else key[1],
            "excerpt": excerpt(d.page_content),
            "url": d.metadata.get("url", "") if web else "",
            "type": "web" if web else "private_kb",
        })
    return citations


def memory_text(state: AgentState) -> str:
    turns = (state.get("memory") or [])[-settings.memory_turns:]
    return "\n\n".join(f"User: {t['question']}\nAssistant: {t['answer']}" for t in turns)


# ---- Memory nodes ----

def contextualize_node(prompt: str):
    def contextualize(state: AgentState):
        if not state.get("memory"):
            return {"trace": add_trace(state, "Memory → new conversation")}
        out, fb = structured(
            QueryRewrite,
            prompt.format(history=memory_text(state), question=state["user_question"]),
            QueryRewrite(query=state["user_question"]),
        )
        return {
            "question": out.query,
            "current_query": out.query,
            "trace": add_trace(state, f"Memory → standalone question: {out.query}{fallback_note(fb)}"),
        }
    return contextualize


def commit_memory(state: AgentState):
    turn = {
        "question": state["user_question"],
        "answer": state["answer"],
        "source_used": state["source_used"],
        "citations": state.get("citations", []),
    }
    return {"memory": [turn], "trace": add_trace(state, "Memory → conversation saved")}


# ---- Nodes ----

def router_node(prompt: str):
    def route_question(state: AgentState):
        decision, fb = structured(RouteDecision, prompt.format(question=state["question"]), RouteDecision(route="kb"))
        return {"source_used": decision.route, "trace": add_trace(state, f"Router → {decision.route.upper()}{fallback_note(fb)}")}
    return route_question


def retrieve_node(namespace: str):
    def retrieve_kb(state: AgentState):
        docs = get_retriever(namespace).invoke(state["current_query"])
        return {"kb_docs": docs, "trace": add_trace(state, f"Private KB retrieval → {len(docs)} chunks")}
    return retrieve_kb


def grade_kb_node(prompt: str):
    def grade_kb(state: AgentState):
        grade, fb = structured(
            EvidenceGrade,
            prompt.format(question=state["question"], context=format_docs(state["kb_docs"])),
            EvidenceGrade(grade="weak"),
        )
        return {"kb_grade": grade.grade, "trace": add_trace(state, f"KB evidence grade → {grade.grade.upper()}{fallback_note(fb)}")}
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
            citations.append({"title": title or url, "page": None, "excerpt": excerpt(content), "url": url, "type": "web"})
    else:
        lines.append(str(result))
    return {
        "web_results": truncate("\n\n".join(lines)),
        "citations": citations,
        "source_used": "web",
        "trace": add_trace(state, "Web fallback → Tavily search"),
    }


def grade_web_node(prompt: str):
    def grade_web(state: AgentState):
        grade, fb = structured(
            EvidenceGrade,
            prompt.format(question=state["question"], evidence=state["web_results"]),
            EvidenceGrade(grade="weak"),
        )
        return {"web_grade": grade.grade, "trace": add_trace(state, f"Web evidence grade → {grade.grade.upper()}{fallback_note(fb)}")}
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
        context = format_docs(state["kb_docs"])
        answer = text_of(llm().invoke(prompt.format(question=state["question"], context=context)))
        return {
            "answer": answer,
            "source_used": "private_kb",
            "citations": doc_citations(state["kb_docs"]),
            "context": context,
            "support_retries": 0,
            "trace": add_trace(state, "Answer generation → PRIVATE KB"),
        }
    return generate_from_kb


def generate_web_node(prompt: str):
    def generate_from_web(state: AgentState):
        answer = text_of(llm().invoke(prompt.format(question=state["question"], evidence=state["web_results"])))
        return {
            "answer": answer,
            "source_used": "web_search",
            "context": state["web_results"],
            "support_retries": 0,
            "trace": add_trace(state, "Answer generation → WEB SEARCH"),
        }
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
            "citations": [],
            "trace": add_trace(state, "Stopped → insufficient reliable evidence"),
        }
    return insufficient


# ---- Self-check nodes ----

def check_support_node(prompt: str):
    def check_support(state: AgentState):
        # Unparseable verdict counts as unsupported: never show an unverified HR answer.
        out, fb = structured(
            SupportDecision,
            prompt.format(question=state["question"], answer=state["answer"], context=state["context"]),
            SupportDecision(status="no_support"),
        )
        return {
            "support_status": out.status,
            "support_evidence": out.evidence,
            "trace": add_trace(state, f"Support check → {out.status.upper()}{fallback_note(fb)}"),
        }
    return check_support


def revise_node(prompt: str):
    def revise_answer(state: AgentState):
        answer = text_of(llm().invoke(prompt.format(question=state["question"], answer=state["answer"], context=state["context"])))
        return {
            "answer": answer,
            "support_retries": state["support_retries"] + 1,
            "trace": add_trace(state, "Revised answer for grounding"),
        }
    return revise_answer


def check_usefulness_node(prompt: str):
    def check_usefulness(state: AgentState):
        # The answer is already grounded at this point, so an unparseable verdict keeps it.
        out, fb = structured(
            UsefulnessDecision,
            prompt.format(question=state["question"], answer=state["answer"]),
            UsefulnessDecision(status="useful", reason="usefulness check unavailable"),
        )
        return {
            "usefulness": out.status,
            "use_reason": out.reason,
            "trace": add_trace(state, f"Usefulness check → {out.status.upper()}{fallback_note(fb)}"),
        }
    return check_usefulness


# ---- Graded-retrieval nodes (CloudOps) ----
# Retrieved chunks and web results are graded one batch at a time; only relevant documents
# are used for generation and cited. Internal and web queries have separate rewrite budgets.

def triage_node(prompt: str):
    def triage(state: AgentState):
        out, fb = structured(Triage, prompt.format(question=state["question"]), Triage(route="kb"))
        details = " · ".join(x for x in (out.severity if out.severity != "none" else "", out.service) if x)
        return {
            "source_used": out.route,
            "triage": out.model_dump(exclude={"route"}),
            "trace": add_trace(state, f"Triage → {out.route.upper()}{f' · {details}' if details else ''}{fallback_note(fb)}"),
        }
    return triage


def retrieve_candidates_node(namespace: str):
    def retrieve_internal(state: AgentState):
        docs = get_retriever(namespace).invoke(state["current_query"])
        return {
            "candidate_docs": docs,
            "relevant_docs": [],
            "source_mode": "internal",
            "trace": add_trace(state, f"Private KB retrieval → {len(docs)} chunks"),
        }
    return retrieve_internal


def search_web_docs(state: AgentState):
    query = state.get("web_query") or state["question"]
    result = web_search_tool().invoke({"query": query})
    items = result.get("results", []) if isinstance(result, dict) else []
    docs = [
        Document(
            page_content=item.get("content", ""),
            metadata={"source_type": "web", "url": item.get("url", ""), "title": item.get("title", "")},
        )
        for item in items
        if item.get("content")
    ]
    return {
        "candidate_docs": docs,
        "relevant_docs": [],
        "source_mode": "web",
        "trace": add_trace(state, f"Web search → {len(docs)} results"),
    }


def grade_documents_node(prompt: str):
    def grade_documents(state: AgentState):
        docs = state["candidate_docs"]
        if not docs:
            return {"relevant_docs": [], "trace": add_trace(state, f"Relevance grade ({state['source_mode']}) → 0/0 relevant")}
        listing = "\n\n".join(
            f"[{i}] {source_name(d)}\n{truncate(d.page_content, 2500)}" for i, d in enumerate(docs, 1)
        )
        # Unparseable verdict keeps every document: the support check still guards the answer.
        out, fb = structured(
            RelevantDocuments,
            prompt.format(question=state["question"], documents=listing),
            RelevantDocuments(relevant=list(range(1, len(docs) + 1))),
        )
        relevant = [docs[i - 1] for i in dict.fromkeys(out.relevant) if 1 <= i <= len(docs)]
        return {
            "relevant_docs": relevant,
            "trace": add_trace(
                state, f"Relevance grade ({state['source_mode']}) → {len(relevant)}/{len(docs)} relevant{fallback_note(fb)}"
            ),
        }
    return grade_documents


def rewrite_internal_node(prompt: str):
    def rewrite_internal(state: AgentState):
        out, fb = structured(
            QueryRewrite,
            prompt.format(question=state["question"], previous=state["current_query"]),
            QueryRewrite(query=state["question"]),
        )
        return {
            "current_query": out.query,
            "retrieval_rewrites": state["retrieval_rewrites"] + 1,
            "trace": add_trace(state, f"Internal query rewrite → {out.query}{fallback_note(fb)}"),
        }
    return rewrite_internal


def rewrite_web_node(prompt: str):
    def rewrite_web(state: AgentState):
        out, fb = structured(
            QueryRewrite,
            prompt.format(question=state["question"], previous=state.get("web_query", "")),
            QueryRewrite(query=state["question"]),
        )
        return {
            "web_query": out.query,
            "web_rewrites": state["web_rewrites"] + 1,
            "trace": add_trace(state, f"Web query → {out.query}{fallback_note(fb)}"),
        }
    return rewrite_web


def generate_evidence_node(prompt: str):
    def generate_from_evidence(state: AgentState):
        docs = state["relevant_docs"]
        context = format_docs(docs)
        source = "private_kb" if state["source_mode"] == "internal" else "web_search"
        answer = text_of(llm().invoke(prompt.format(question=state["question"], context=context)))
        return {
            "answer": answer,
            "source_used": source,
            "citations": doc_citations(docs),
            "context": context,
            "support_retries": 0,
            "trace": add_trace(state, f"Answer generation → {'PRIVATE KB' if source == 'private_kb' else 'WEB SEARCH'}"),
        }
    return generate_from_evidence


def after_grading(state: AgentState) -> Literal["generate", "rewrite_internal", "rewrite_web", "insufficient"]:
    if state["relevant_docs"]:
        return "generate"
    if state["source_mode"] == "internal":
        return "rewrite_internal" if state["retrieval_rewrites"] < settings.max_retrieval_rewrites else "rewrite_web"
    return "rewrite_web" if state["web_rewrites"] < settings.max_web_rewrites else "insufficient"


def after_graded_usefulness(state: AgentState) -> Literal["commit_memory", "rewrite_internal", "rewrite_web", "insufficient"]:
    if state["usefulness"] == "useful":
        return "commit_memory"
    if state["source_mode"] == "internal":
        return "rewrite_internal" if state["retrieval_rewrites"] < settings.max_retrieval_rewrites else "rewrite_web"
    return "rewrite_web" if state["web_rewrites"] < settings.max_web_rewrites else "insufficient"


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


def after_support(state: AgentState) -> Literal["check_usefulness", "revise_answer", "insufficient"]:
    status = state["support_status"]
    if status == "fully_supported":
        return "check_usefulness"
    if state["support_retries"] < settings.max_support_retries:
        return "revise_answer"
    # After revision: a partially supported answer had its unsupported claims removed;
    # an unsupported one is never shown.
    return "check_usefulness" if status == "partially_supported" else "insufficient"


def after_usefulness(state: AgentState) -> Literal["commit_memory", "rewrite_query", "insufficient"]:
    if state["usefulness"] == "useful":
        return "commit_memory"
    if state["retry_count"] < settings.max_retries:
        return "rewrite_query"
    return "insufficient"
