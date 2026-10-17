"""Maps each domain to its own workflow and knowledge base namespace."""
from dataclasses import dataclass
from typing import Any
from app.core.config import get_settings
from app.rag.common.memory import get_checkpointer, thread_config
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
    "hr": Domain("hr", "HR Policy", settings.hr_namespace, build_hr_graph(get_checkpointer())),
}

DEFAULT_DOMAIN = "hr"


def get_domain(name: str) -> Domain:
    """Raise KeyError for an unknown domain."""
    return DOMAINS[name]


def ask(domain: Domain, question: str, thread_id: str):
    return domain.graph.invoke(initial_state(question), config=thread_config(domain.name, thread_id))


def get_history(domain: Domain, thread_id: str) -> list[dict]:
    snapshot = domain.graph.get_state(thread_config(domain.name, thread_id))
    return list(snapshot.values.get("memory", []))


def clear_history(domain: Domain, thread_id: str) -> None:
    get_checkpointer().delete_thread(thread_config(domain.name, thread_id)["configurable"]["thread_id"])
