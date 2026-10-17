from langchain_core.messages import AIMessage
from app.core.llm import text_of
from app.rag.common.state import initial_state
from app.rag.hr.graph import build_graph


def run(question):
    return build_graph().invoke(initial_state(question))


def test_greeting_goes_direct(patch_rag):
    patch_rag([{"route": "direct"}], text="Hello!")
    result = run("Hi there")
    assert result["source_used"] == "direct"
    assert result["answer"] == "Hello!"
    assert result["trace"] == ["Router → DIRECT", "Direct response → no retrieval"]


def test_good_kb_evidence_answers_from_private_kb(patch_rag):
    fake = patch_rag([{"route": "kb"}, {"grade": "good"}], text="20 days.")
    result = run("How many annual leave days do employees receive?")
    assert result["source_used"] == "private_kb"
    assert result["answer"] == "20 days."
    # Citations deduplicated by file name, including Linux-style source paths.
    assert result["citations"] == [{"title": "company_hr_handbook.md", "url": "", "type": "private_kb"}]
    assert "[Source: company_hr_handbook.md]" in fake.prompts[-1]


def test_weak_kb_falls_back_to_web(patch_rag):
    patch_rag([{"route": "kb"}, {"grade": "weak"}, {"grade": "good"}], text="Public holidays...")
    result = run("What are the latest public holiday rules in France?")
    assert result["source_used"] == "web_search"
    assert result["citations"][0]["url"] == "https://example.gov"
    assert "Web fallback → Tavily search" in result["trace"]


def test_weak_everywhere_rewrites_once_then_stops(patch_rag):
    patch_rag(
        [{"route": "kb"}, {"grade": "weak"}, {"grade": "weak"}, {"grade": "weak"}, {"grade": "weak"}],
        text="rewritten query",
    )
    result = run("What happens if mine is wrong?")
    assert result["source_used"] == "insufficient_evidence"
    assert result["retry_count"] == 1
    assert result["current_query"] == "rewritten query"
    assert result["trace"][-1] == "Stopped → insufficient reliable evidence"


def test_text_of_handles_strings_and_blocks():
    assert text_of(AIMessage(content="  plain  ")) == "plain"
    assert text_of(AIMessage(content=[{"type": "text", "text": "a"}, "b"])) == "ab"
