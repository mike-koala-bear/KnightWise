"""LLM-stack health endpoint.

Exposes which model the coach is wired to and whether a real OpenAI call
would be made (vs. falling back to the deterministic stub). The frontend
uses this to show a small "AI coach: live" badge so the student knows when
their feedback is real vs. stubbed.

Does NOT make a network call — it only inspects local configuration.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ..llm.router import MODEL, health

router = APIRouter()


class LLMHealth(BaseModel):
    model: str
    live: bool
    reason: str


@router.get("/llm/health", response_model=LLMHealth)
def llm_health() -> LLMHealth:
    """Report the LLM stack's configuration without calling the live API."""
    state = health()
    return LLMHealth(
        model=str(state["model"]),
        live=bool(state["live"]),
        reason=str(state["reason"]),
    )


__all__ = ["router", "MODEL"]
