import pytest
from fastapi.testclient import TestClient
from app.api import chat
from app.main import app

client = TestClient(app)

FAKE_RESULT = {
    "answer": "20 days.",
    "source_used": "private_kb",
    "trace": ["Router → KB"],
    "citations": [],
    "current_query": "leave days",
}


@pytest.fixture
def fake_ask(monkeypatch):
    calls = []

    def ask(domain, question):
        calls.append((domain.name, question))
        return FAKE_RESULT

    monkeypatch.setattr(chat, "ask", ask)
    return calls


def test_health():
    assert client.get("/api/health").json()["status"] == "ok"


def test_domains_lists_hr():
    data = client.get("/api/domains").json()
    assert data["default"] == "hr"
    assert {"name": "hr", "label": "HR Policy"} in data["domains"]


def test_chat_by_domain(fake_ask):
    res = client.post("/api/chat/hr", json={"question": "leave days"})
    assert res.status_code == 200
    assert res.json()["answer"] == "20 days."
    assert res.json()["domain"] == "hr"
    assert fake_ask == [("hr", "leave days")]


def test_legacy_chat_route_uses_default_domain(fake_ask):
    res = client.post("/api/chat", json={"question": "leave days"})
    assert res.status_code == 200
    assert fake_ask == [("hr", "leave days")]


def test_unknown_domain_is_404(fake_ask):
    res = client.post("/api/chat/finance", json={"question": "budget"})
    assert res.status_code == 404
    assert fake_ask == []


def test_ingest_requires_admin_key():
    res = client.post("/api/ingest/hr", files={"file": ("a.txt", b"hello")}, headers={"X-Admin-Key": "wrong"})
    assert res.status_code == 401


def test_home_page_renders():
    res = client.get("/")
    assert res.status_code == 200
    assert "HR Policy" in res.text
