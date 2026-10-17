import os
import tempfile
from collections import deque

# Must be set before any app module reads the settings.
os.environ["AUDIT_DB_PATH"] = os.path.join(tempfile.mkdtemp(), "audit_test.db")
os.environ["ADMIN_API_KEY"] = "test-admin-key"
os.environ["MAX_RETRIES"] = "1"

import pytest
from langchain_core.documents import Document
from langchain_core.messages import AIMessage
from app.rag.common import nodes


class FakeStructured:
    def __init__(self, parent, schema):
        self.parent, self.schema = parent, schema

    def invoke(self, prompt):
        self.parent.prompts.append(prompt)
        return self.schema(**self.parent.structured.popleft())


class FakeLLM:
    """Returns queued structured outputs in order; plain invokes return list-of-blocks content
    like Gemini chat models do."""

    def __init__(self, structured=(), text="fake answer"):
        self.structured = deque(structured)
        self.text = text
        self.prompts = []

    def with_structured_output(self, schema, **kwargs):
        return FakeStructured(self, schema)

    def invoke(self, prompt):
        self.prompts.append(prompt)
        return AIMessage(content=[{"type": "text", "text": self.text}])


class FakeRetriever:
    def __init__(self, docs):
        self.docs = docs

    def invoke(self, query):
        return self.docs


class FakeWebSearch:
    def invoke(self, payload):
        return {
            "answer": "Public answer",
            "results": [{"title": "Gov page", "url": "https://example.gov", "content": "Public info"}],
        }


@pytest.fixture
def kb_docs():
    return [
        Document(page_content="Employees receive 20 annual leave days.",
                 metadata={"source": r"C:\data\documents\hr\company_hr_handbook.md", "filename": "company_hr_handbook.md"}),
        Document(page_content="Leave requests go through the HR portal.",
                 metadata={"source": "/app/data/documents/hr/company_hr_handbook.md"}),
    ]


@pytest.fixture
def patch_rag(monkeypatch, kb_docs):
    """Patch LLM, retriever and web search; returns a function that installs a FakeLLM."""
    monkeypatch.setattr(nodes, "get_retriever", lambda namespace: FakeRetriever(kb_docs))
    monkeypatch.setattr(nodes, "web_search_tool", lambda: FakeWebSearch())

    def install(structured, text="fake answer"):
        fake = FakeLLM(structured, text)
        monkeypatch.setattr(nodes, "llm", lambda: fake)
        return fake

    return install
