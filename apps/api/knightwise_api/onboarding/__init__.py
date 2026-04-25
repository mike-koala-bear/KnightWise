"""Onboarding skill test: estimate the user's starting Elo with ~12 puzzles.

The whole personalization stack downstream (drill difficulty, weakness ranking,
daily Warp dosing, Maia-3 elo input) depends on a calibrated rating estimate.
Without it everything is guessing.

Public surface:
- :func:`update_glicko1`     — apply one puzzle attempt to (mu, sigma)
- :func:`pick_next_puzzle`   — adaptive selector
- :func:`is_session_complete` — stopping rule (n attempts OR sigma converged)
"""

from .glicko import (
    DEFAULT_MU,
    DEFAULT_SIGMA,
    GLICKO_FLOOR_SIGMA,
    GlickoEstimate,
    update_glicko1,
)
from .selector import is_session_complete, pick_next_puzzle

__all__ = [
    "DEFAULT_MU",
    "DEFAULT_SIGMA",
    "GLICKO_FLOOR_SIGMA",
    "GlickoEstimate",
    "is_session_complete",
    "pick_next_puzzle",
    "update_glicko1",
]
