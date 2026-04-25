"""Engine-stack health endpoint.

Reports which Maia adapter is currently active (``maia3``, ``stockfish``, or
``null``). The frontend uses this to show a small badge so the student knows
whether their weakness analysis is using the real human-trained Maia-3 net or
the cheaper Stockfish-Elo approximation.

Does NOT call the network or load weights eagerly — it asks
:func:`knightwise_api.engine.maia.get_maia` for the configured adapter and
reads its type. Loading the actual ONNX session is deferred to first
prediction call, so this endpoint is cheap to hit.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ..engine.maia import adapter_name, get_maia

router = APIRouter()


class EngineHealth(BaseModel):
    maia_adapter: str
    maia_real: bool


@router.get("/engine/health", response_model=EngineHealth)
def engine_health() -> EngineHealth:
    """Report which Maia adapter is wired up right now."""
    name = adapter_name(get_maia())
    return EngineHealth(maia_adapter=name, maia_real=name == "maia3")


__all__ = ["router"]
