"""LLM router tests — exercise the stub paths (no network)."""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient
from knightwise_api.llm import router as router_module
from knightwise_api.llm.router import MODEL, generate, health
from knightwise_api.main import create_app
from knightwise_api.settings import settings


def test_model_is_locked_to_gpt_4o_mini():
    """The product decision is to ONLY use gpt-4o-mini.

    Guard against an accidental edit that swaps the model out — every coach
    note, lesson hint, and weakness explanation must come from this model.
    """
    assert MODEL == "gpt-4o-mini"


def test_stub_when_no_api_key(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", None)
    out = generate("hello", purpose="coach_note")
    assert out.startswith("(stub)")


def test_stub_for_each_purpose(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", None)
    for purpose in ("coach_note", "lesson_hint", "weakness_explain", "test"):
        out = generate("x", purpose=purpose)  # type: ignore[arg-type]
        assert out, f"empty stub for purpose={purpose}"


def test_health_no_key(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", None)
    state = health()
    assert state == {"model": "gpt-4o-mini", "live": False, "reason": "no_api_key"}


def test_health_live_when_key_present(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "sk-test-stub")
    state = health()
    assert state["model"] == "gpt-4o-mini"
    assert state["live"] is True
    assert state["reason"] == "ok"


def test_health_endpoint_shape(monkeypatch):
    """`GET /v1/llm/health` reports model + live without calling the network."""
    monkeypatch.setattr(settings, "openai_api_key", None)
    client = TestClient(create_app())
    res = client.get("/v1/llm/health")
    assert res.status_code == 200
    body = res.json()
    assert body == {"model": "gpt-4o-mini", "live": False, "reason": "no_api_key"}


def test_generate_calls_openai_with_locked_model(monkeypatch):
    """When a key is present, we hit OpenAI with model=gpt-4o-mini."""
    monkeypatch.setattr(settings, "openai_api_key", "sk-test-stub")

    captured: dict[str, Any] = {}

    class _Choice:
        def __init__(self, content: str) -> None:
            self.message = type("M", (), {"content": content})()

    class _Response:
        def __init__(self, content: str) -> None:
            self.choices = [_Choice(content)]

    class _Completions:
        def create(self, **kwargs: Any) -> _Response:
            captured.update(kwargs)
            return _Response("real coach note")

    class _Chat:
        completions = _Completions()

    class _FakeOpenAI:
        def __init__(self, api_key: str | None = None) -> None:
            captured["api_key"] = api_key
            self.chat = _Chat()

    fake_openai = type("FakeOpenAIModule", (), {"OpenAI": _FakeOpenAI})
    monkeypatch.setitem(__import__("sys").modules, "openai", fake_openai)

    out = generate("prompt", purpose="coach_note")

    assert out == "real coach note"
    assert captured["model"] == "gpt-4o-mini"
    assert captured["api_key"] == "sk-test-stub"
    # System prompt is wired through, not blank.
    messages = captured["messages"]
    assert messages[0]["role"] == "system"
    assert messages[0]["content"]
    assert messages[1] == {"role": "user", "content": "prompt"}


def test_generate_falls_back_on_openai_exception(monkeypatch):
    """If OpenAI raises, we fall back to the stub instead of 500ing."""
    monkeypatch.setattr(settings, "openai_api_key", "sk-test-stub")

    class _Completions:
        def create(self, **kwargs: Any) -> Any:
            raise RuntimeError("rate limited")

    class _Chat:
        completions = _Completions()

    class _FakeOpenAI:
        def __init__(self, api_key: str | None = None) -> None:
            self.chat = _Chat()

    fake_openai = type("FakeOpenAIModule", (), {"OpenAI": _FakeOpenAI})
    monkeypatch.setitem(__import__("sys").modules, "openai", fake_openai)

    out = generate("prompt", purpose="coach_note")
    assert out.startswith("(stub)"), out


def test_module_constant_is_imported_by_warp(monkeypatch):
    """Sanity: the warp composer pulls `generate` from the same router module
    that exposes MODEL — there's only one LLM entry point."""
    from knightwise_api.warp import composer

    assert composer.generate is router_module.generate


@pytest.fixture(autouse=True)
def _restore_openai_module():
    """Make sure other tests don't see our injected fake `openai` module."""
    yield
    import sys

    sys.modules.pop("openai", None)
