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
    "memory": [{"question": "leave days", "answer": "20 days.", "source_used": "private_kb"}],
}


@pytest.fixture
def fake_ask(monkeypatch):
    calls = []

    def ask(domain, question, thread_id):
        calls.append((domain.name, question, thread_id))
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
    res = client.post("/api/chat/hr", json={"question": "leave days", "thread_id": "abc-123"})
    assert res.status_code == 200
    data = res.json()
    assert data["answer"] == "20 days."
    assert data["domain"] == "hr"
    assert data["thread_id"] == "abc-123"
    assert data["memory_turns"] == 1
    assert fake_ask == [("hr", "leave days", "abc-123")]


def test_chat_without_thread_id_creates_one(fake_ask):
    res = client.post("/api/chat/hr", json={"question": "leave days"})
    thread_id = res.json()["thread_id"]
    assert len(thread_id) == 32
    assert fake_ask == [("hr", "leave days", thread_id)]


def test_invalid_thread_id_is_rejected(fake_ask):
    res = client.post("/api/chat/hr", json={"question": "leave days", "thread_id": "../etc"})
    assert res.status_code == 422
    assert fake_ask == []


def test_legacy_chat_route_uses_default_domain(fake_ask):
    res = client.post("/api/chat", json={"question": "leave days", "thread_id": "abc-123"})
    assert res.status_code == 200
    assert fake_ask == [("hr", "leave days", "abc-123")]


def test_conversations_are_listed_per_domain(fake_ask):
    client.post("/api/chat/hr", json={"question": "How many leave days?", "thread_id": "conv-a"})
    client.post("/api/chat/hr", json={"question": "And sick leave?", "thread_id": "conv-a"})
    client.post("/api/chat/hr", json={"question": "Remote work policy?", "thread_id": "conv-b"})

    sessions = {s["thread_id"]: s for s in client.get("/api/sessions/hr").json()["sessions"]}
    assert sessions["conv-a"]["title"] == "How many leave days?"   # title = first question
    assert sessions["conv-a"]["turns"] == 2
    assert sessions["conv-b"]["turns"] == 1

    client.delete("/api/sessions/hr/conv-a")
    remaining = [s["thread_id"] for s in client.get("/api/sessions/hr").json()["sessions"]]
    assert "conv-a" not in remaining and "conv-b" in remaining
    assert client.get("/api/sessions/finance").status_code == 404


def test_session_history_and_delete():
    assert client.get("/api/sessions/hr/unknown-thread").json()["turns"] == []
    assert client.delete("/api/sessions/hr/unknown-thread").json()["deleted"] is True
    assert client.get("/api/sessions/finance/abc").status_code == 404


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
