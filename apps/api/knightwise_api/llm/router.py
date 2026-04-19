"""Single LLM router. All GPT-4o-mini calls go through here.

If OPENAI_API_KEY is not set, returns a canned stub — useful for PR #1 and for tests.
Real coach prompts + OpenAI wiring land in PR #4.
"""

from __future__ import annotations

from typing import Literal

from ..settings import settings

Purpose = Literal["coach_note", "lesson_hint", "weakness_explain", "test"]

_STUBS: dict[Purpose, str] = {
    "coach_note": "(stub) Your last blunder hangs the bishop to a tactic you missed. Drill: `tactics/hanging-piece-01`.",
    "lesson_hint": "(stub) Look for undefended pieces and check every move your opponent can make before yours.",
    "weakness_explain": "(stub) You lose ~40cp per move when opponent has a discovered attack pattern.",
    "test": "(stub) LLM router reachable.",
}


def generate(prompt: str, purpose: Purpose = "coach_note") -> str:
    """Produce a short text response.

    PR #1: returns stub. PR #4: calls `openai.chat.completions.create` with model=gpt-4o-mini.
    """
    del prompt  # unused in stub
    if not settings.openai_api_key:
        return _STUBS[purpose]
    # PR #4 will replace this with the real OpenAI call.
    return _STUBS[purpose]
