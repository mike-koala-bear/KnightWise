"""Single LLM router. All GPT-4o-mini calls go through here.

If OPENAI_API_KEY is not set, returns a canned stub — useful for tests and
offline dev. When the key is present, we call `openai.chat.completions.create`
with `model=gpt-4o-mini`.

Keep this module the ONLY place we touch the OpenAI SDK so the model can be
swapped in one spot.
"""

from __future__ import annotations

import logging
from typing import Literal

from ..settings import settings

logger = logging.getLogger(__name__)

#: The single LLM model used for ALL coaching calls. Locked by product
#: decision — do not change without updating tests + cost docs.
MODEL: str = "gpt-4o-mini"

Purpose = Literal["coach_note", "lesson_hint", "weakness_explain", "test"]

_SYSTEM_PROMPTS: dict[Purpose, str] = {
    "coach_note": (
        "You are a warm, concise chess coach helping an adult improver gain "
        "rating fast. The student has just finished a session. Reply with "
        "exactly 2-3 sentences. Sentence 1: name the single biggest weakness "
        "in plain English (no jargon). Sentence 2: name ONE concrete pattern "
        "or check they should run on every move today (e.g. 'before every "
        "move ask: is my back rank safe?'). Sentence 3 (optional): one "
        "sentence of encouragement tied to their improvement, not generic. "
        "Never hedge. Never say 'consider'. Never use bullet points."
    ),
    "lesson_hint": (
        "You are a patient chess tutor. Give a single-sentence hint that "
        "nudges the student toward the correct idea without revealing the "
        "move. Assume they can read a board."
    ),
    "weakness_explain": (
        "You are a chess analyst. In 1-2 sentences, explain why this weakness "
        "tag hurts the player at their rating level. Be specific about the "
        "pattern, not generic."
    ),
    "test": "Reply with exactly: LLM router reachable.",
}

_STUBS: dict[Purpose, str] = {
    "coach_note": (
        "(stub) Your biggest leak is missing back-rank tactics — your king "
        "had no luft in 3 of your last 5 losses. Drill `back-rank-basics` "
        "for 10 minutes today."
    ),
    "lesson_hint": "(stub) Look for undefended pieces and every check first.",
    "weakness_explain": (
        "(stub) At your rating, missed back-rank tactics lose ~120cp per game "
        "because the mating pattern repeats and opponents start to see it."
    ),
    "test": "(stub) LLM router reachable.",
}


def generate(prompt: str, purpose: Purpose = "coach_note") -> str:
    """Produce a short text response for a given coaching purpose.

    Falls back to a deterministic stub when `OPENAI_API_KEY` is absent.
    """
    if not settings.openai_api_key:
        return _STUBS[purpose]

    try:
        from openai import OpenAI
    except ImportError:
        logger.warning("openai package not importable; falling back to stub")
        return _STUBS[purpose]

    client = OpenAI(api_key=settings.openai_api_key)
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPTS[purpose]},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=180,
        )
    except Exception as exc:  # pragma: no cover - network / API errors
        logger.warning("openai call failed: %s; falling back to stub", exc)
        return _STUBS[purpose]

    content = response.choices[0].message.content or ""
    return content.strip() or _STUBS[purpose]


def health() -> dict[str, str | bool]:
    """Probe the LLM stack. Returns whether a real model call would be made.

    Does NOT call the live API — just reports configuration. The frontend can
    surface a 'AI coach: live' badge based on this.
    """
    if not settings.openai_api_key:
        return {"model": MODEL, "live": False, "reason": "no_api_key"}
    try:
        import openai  # noqa: F401
    except ImportError:
        return {"model": MODEL, "live": False, "reason": "openai_not_installed"}
    return {"model": MODEL, "live": True, "reason": "ok"}
