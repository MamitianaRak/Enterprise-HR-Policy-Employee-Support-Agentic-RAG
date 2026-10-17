import operator
from typing import Annotated, List, Literal
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langchain_core.documents import Document


class RouteDecision(BaseModel):
    route: Literal["kb", "direct"] = Field(description="kb for domain questions; direct for greetings/simple chat")


class EvidenceGrade(BaseModel):
    grade: Literal["good", "weak"] = Field(description="Whether evidence is sufficient to answer")


class QueryRewrite(BaseModel):
    query: str = Field(description="Standalone question or search query")


class SupportDecision(BaseModel):
    status: Literal["fully_supported", "partially_supported", "no_support"]
    evidence: List[str] = Field(default_factory=list, description="Short supporting excerpts")


class UsefulnessDecision(BaseModel):
    status: Literal["useful", "not_useful"]
    reason: str = ""


class MemoryTurn(TypedDict):
    question: str
    answer: str
    source_used: str
    citations: List[dict]


class AgentState(TypedDict):
    user_question: str  # raw message as typed by the user
    question: str       # standalone version, after contextualization
    current_query: str
    kb_docs: List[Document]
    web_results: str
    kb_grade: str
    web_grade: str
    answer: str
    source_used: str
    retry_count: int
    trace: List[str]
    citations: List[dict]
    # Self-check of the generated answer
    context: str
    support_status: str
    support_evidence: List[str]
    support_retries: int
    usefulness: str
    use_reason: str
    # Accumulates across turns of the same thread (persisted by the checkpointer).
    memory: Annotated[List[MemoryTurn], operator.add]


def initial_state(question: str) -> AgentState:
    """Per-turn fields are reset; memory=[] adds nothing, so history is kept."""
    return {
        "user_question": question,
        "question": question,
        "current_query": question,
        "kb_docs": [],
        "web_results": "",
        "kb_grade": "",
        "web_grade": "",
        "answer": "",
        "source_used": "",
        "retry_count": 0,
        "trace": [],
        "citations": [],
        "context": "",
        "support_status": "",
        "support_evidence": [],
        "support_retries": 0,
        "usefulness": "",
        "use_reason": "",
        "memory": [],
    }
