"""LLM router tests — exercise the stub paths (no network)."""

from knightwise_api.llm.router import generate
from knightwise_api.settings import settings


def test_stub_when_no_api_key(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", None)
    out = generate("hello", purpose="coach_note")
    assert out.startswith("(stub)")


def test_stub_for_each_purpose(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", None)
    for purpose in ("coach_note", "lesson_hint", "weakness_explain", "test"):
        out = generate("x", purpose=purpose)  # type: ignore[arg-type]
        assert out, f"empty stub for purpose={purpose}"
