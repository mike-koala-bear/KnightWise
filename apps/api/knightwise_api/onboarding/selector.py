"""Adaptive puzzle selector + stopping rule for the onboarding skill test.

Selector strategy (intentionally simple — readable beats clever for a 12-item test):

1. Filter to onboarding-tagged puzzles the user has not yet seen this session.
2. Score each candidate by ``-abs(rating - mu)`` so the puzzle nearest the
   current estimate wins. Maximally informative: if mu = 1500 and sigma = 200,
   a 1500 puzzle is the highest-information attempt by Fisher information.
3. Tie-break by larger rating first — a tied higher-rated puzzle gives a
   slightly cleaner signal because the success probability moves further from
   0.5 in the first attempt of a session.

This is NOT full information-theoretic CAT. We trade ~5% efficiency for a
selector that is trivially auditable and produces deterministic ordering for
a given user pool.

Stopping rule (:func:`is_session_complete`):
- ``MAX_ATTEMPTS`` reached, OR
- sigma has fallen below :data:`GLICKO_CONVERGED_SIGMA` AND at least
  :data:`MIN_ATTEMPTS` items answered (avoids a lucky-streak early exit).
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from .glicko import GLICKO_CONVERGED_SIGMA, GlickoEstimate

MIN_ATTEMPTS: int = 6
MAX_ATTEMPTS: int = 12


@dataclass(slots=True, frozen=True)
class Candidate:
    """Lightweight puzzle row used by the selector. Avoids importing the ORM
    model so this stays unit-testable without a DB session."""

    id: int
    rating: int


def pick_next_puzzle(
    candidates: Iterable[Candidate],
    *,
    estimate: GlickoEstimate,
    seen_puzzle_ids: Sequence[int] = (),
) -> Candidate | None:
    """Pick the next puzzle nearest the user's current Elo estimate.

    Returns ``None`` when no unseen candidate is available (the caller should
    treat that as "skill test exhausted" and finalise the session).
    """
    seen = set(seen_puzzle_ids)
    pool = [c for c in candidates if c.id not in seen]
    if not pool:
        return None
    # min by abs distance, tie-broken by *higher* rating (negative for ascending sort).
    pool.sort(key=lambda c: (abs(c.rating - estimate.mu), -c.rating))
    return pool[0]


def is_session_complete(
    *,
    attempts_so_far: int,
    estimate: GlickoEstimate,
) -> bool:
    if attempts_so_far >= MAX_ATTEMPTS:
        return True
    if attempts_so_far >= MIN_ATTEMPTS and estimate.sigma <= GLICKO_CONVERGED_SIGMA:
        return True
    return False


__all__ = [
    "MAX_ATTEMPTS",
    "MIN_ATTEMPTS",
    "Candidate",
    "is_session_complete",
    "pick_next_puzzle",
]
