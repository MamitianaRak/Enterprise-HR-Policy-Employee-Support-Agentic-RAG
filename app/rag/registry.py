"""Maps each domain to its own workflow and knowledge base namespace."""
from dataclasses import dataclass
from typing import Any
from app.core.config import get_settings
from app.rag.common.state import initial_state
from app.rag.hr.graph import build_graph as build_hr_graph

settings = get_settings()


@dataclass(frozen=True)
class Domain:
    name: str
    label: str
    namespace: str
    graph: Any


DOMAINS: dict[str, Domain] = {
    "hr": Domain("hr", "HR Policy", settings.hr_namespace, build_hr_graph()),
}

DEFAULT_DOMAIN = "hr"


def get_domain(name: str) -> Domain:
    """Raise KeyError for an unknown domain."""
    return DOMAINS[name]


def ask(domain: Domain, question: str):
    return domain.graph.invoke(initial_state(question))
