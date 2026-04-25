"""Onboarding skill-test endpoints.

Flow (single user, no separate "session" entity needed — the session is
implicit while ``users.onboarding_completed_at IS NULL``):

1. ``POST /v1/onboarding/start``     — initialise mu/sigma to defaults if unset.
2. ``GET  /v1/onboarding/next``      — adaptive next puzzle (or null when done).
3. ``POST /v1/onboarding/attempt``   — score the move, update Glicko, append audit row.
4. ``POST /v1/onboarding/finish``    — stamp ``onboarding_completed_at`` (idempotent).

The user sends ``move_uci`` and the server is the source of truth on
correctness. Front-end MUST NOT decide correctness itself.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import OnboardingAttempt, Puzzle, User
from ..onboarding import (
    DEFAULT_MU,
    DEFAULT_SIGMA,
    GlickoEstimate,
    is_session_complete,
    pick_next_puzzle,
    update_glicko1,
)
from ..onboarding.selector import MAX_ATTEMPTS, MIN_ATTEMPTS, Candidate

router = APIRouter(tags=["onboarding"])

DBSession = Annotated[Session, Depends(get_db)]

ONBOARDING_THEME = "onboarding"


class OnboardingStateOut(BaseModel):
    user_id: int
    rating_mu: float
    rating_sigma: float
    attempts_so_far: int
    completed_at: str | None
    min_attempts: int = MIN_ATTEMPTS
    max_attempts: int = MAX_ATTEMPTS


class OnboardingPuzzleOut(BaseModel):
    id: int
    external_id: str | None
    fen: str
    rating: int
    description: str | None


class OnboardingNextOut(BaseModel):
    puzzle: OnboardingPuzzleOut | None
    state: OnboardingStateOut
    done: bool


class AttemptIn(BaseModel):
    user_id: int = Field(..., ge=1)
    puzzle_id: int = Field(..., ge=1)
    move_uci: str = Field(..., min_length=4, max_length=5)
    time_ms: int = Field(0, ge=0, le=60 * 60 * 1000)


class AttemptOut(BaseModel):
    correct: bool
    expected_uci: str
    state: OnboardingStateOut
    done: bool


class FinishIn(BaseModel):
    user_id: int = Field(..., ge=1)


def _require_user(db: Session, user_id: int) -> User:
    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail=f"user not found: {user_id}")
    return user


def _state(db: Session, user: User) -> OnboardingStateOut:
    attempts = (
        db.execute(
            select(func.count(OnboardingAttempt.id)).where(OnboardingAttempt.user_id == user.id)
        ).scalar_one()
    )
    return OnboardingStateOut(
        user_id=user.id,
        rating_mu=float(user.rating_mu if user.rating_mu is not None else DEFAULT_MU),
        rating_sigma=float(user.rating_sigma if user.rating_sigma is not None else DEFAULT_SIGMA),
        attempts_so_far=int(attempts),
        completed_at=user.onboarding_completed_at.isoformat()
        if user.onboarding_completed_at
        else None,
    )


def _seen_ids(db: Session, user_id: int) -> list[int]:
    rows = db.execute(
        select(OnboardingAttempt.puzzle_id).where(OnboardingAttempt.user_id == user_id)
    ).scalars().all()
    return list(rows)


def _onboarding_pool(db: Session) -> list[Candidate]:
    rows = db.execute(select(Puzzle.id, Puzzle.rating, Puzzle.themes)).all()
    pool: list[Candidate] = []
    for pid, rating, themes in rows:
        if themes and ONBOARDING_THEME in themes:
            pool.append(Candidate(id=pid, rating=int(rating)))
    return pool


def _is_done(state: OnboardingStateOut) -> bool:
    if state.completed_at is not None:
        return True
    return is_session_complete(
        attempts_so_far=state.attempts_so_far,
        estimate=GlickoEstimate(mu=state.rating_mu, sigma=state.rating_sigma),
    )


@router.post("/onboarding/start", response_model=OnboardingStateOut)
def onboarding_start(
    db: DBSession,
    user_id: int = Query(..., ge=1),
) -> OnboardingStateOut:
    user = _require_user(db, user_id)
    if user.rating_mu is None:
        user.rating_mu = DEFAULT_MU
    if user.rating_sigma is None:
        user.rating_sigma = DEFAULT_SIGMA
    db.commit()
    db.refresh(user)
    return _state(db, user)


@router.get("/onboarding/next", response_model=OnboardingNextOut)
def onboarding_next(
    db: DBSession,
    user_id: int = Query(..., ge=1),
) -> OnboardingNextOut:
    user = _require_user(db, user_id)
    state = _state(db, user)
    if _is_done(state):
        return OnboardingNextOut(puzzle=None, state=state, done=True)

    pool = _onboarding_pool(db)
    if not pool:
        raise HTTPException(
            status_code=503,
            detail="No onboarding puzzles seeded. Run `seed-onboarding` first.",
        )
    chosen = pick_next_puzzle(
        pool,
        estimate=GlickoEstimate(mu=state.rating_mu, sigma=state.rating_sigma),
        seen_puzzle_ids=_seen_ids(db, user.id),
    )
    if chosen is None:
        return OnboardingNextOut(puzzle=None, state=state, done=True)

    puzzle = db.execute(select(Puzzle).where(Puzzle.id == chosen.id)).scalar_one()
    return OnboardingNextOut(
        puzzle=OnboardingPuzzleOut(
            id=puzzle.id,
            external_id=puzzle.external_id,
            fen=puzzle.fen,
            rating=puzzle.rating,
            description=puzzle.description,
        ),
        state=state,
        done=False,
    )


@router.post("/onboarding/attempt", response_model=AttemptOut)
def onboarding_attempt(req: AttemptIn, db: DBSession) -> AttemptOut:
    user = _require_user(db, req.user_id)
    if user.onboarding_completed_at is not None:
        raise HTTPException(status_code=409, detail="onboarding already completed")

    # Server-side stopping rule: refuse new attempts once the session has
    # converged or hit MAX_ATTEMPTS. The `done` flag in earlier responses is
    # advisory only; this is the authoritative check.
    pre_state = _state(db, user)
    if _is_done(pre_state):
        raise HTTPException(
            status_code=409,
            detail="onboarding session is complete; call /finish",
        )

    # Block duplicate-puzzle submissions so a client cannot rig the rating by
    # re-attempting the same puzzle repeatedly.
    if req.puzzle_id in _seen_ids(db, user.id):
        raise HTTPException(
            status_code=409,
            detail=f"puzzle already attempted: {req.puzzle_id}",
        )

    puzzle = db.execute(select(Puzzle).where(Puzzle.id == req.puzzle_id)).scalar_one_or_none()
    if puzzle is None:
        raise HTTPException(status_code=404, detail=f"puzzle not found: {req.puzzle_id}")
    expected = (puzzle.solution_uci or [""])[0]
    if not expected:
        raise HTTPException(status_code=500, detail="puzzle has no solution")

    correct = req.move_uci.strip().lower() == expected.lower()
    score = 1.0 if correct else 0.0

    current = GlickoEstimate(
        mu=float(user.rating_mu if user.rating_mu is not None else DEFAULT_MU),
        sigma=float(user.rating_sigma if user.rating_sigma is not None else DEFAULT_SIGMA),
    )
    updated = update_glicko1(current, opponent_rating=float(puzzle.rating), score=score)

    user.rating_mu = updated.mu
    user.rating_sigma = updated.sigma
    db.add(
        OnboardingAttempt(
            user_id=user.id,
            puzzle_id=puzzle.id,
            correct=correct,
            time_ms=req.time_ms,
            rating_mu_after=updated.mu,
            rating_sigma_after=updated.sigma,
        )
    )
    db.commit()
    db.refresh(user)

    state = _state(db, user)
    return AttemptOut(
        correct=correct,
        expected_uci=expected,
        state=state,
        done=_is_done(state),
    )


@router.post("/onboarding/finish", response_model=OnboardingStateOut)
def onboarding_finish(req: FinishIn, db: DBSession) -> OnboardingStateOut:
    user = _require_user(db, req.user_id)
    if user.onboarding_completed_at is None:
        # Refuse to stamp completion before the stopping rule is satisfied.
        # Otherwise a client could call start → finish and bypass calibration
        # while keeping the default 1500/350 rating.
        state = _state(db, user)
        if not _is_done(state):
            raise HTTPException(
                status_code=409,
                detail="onboarding session is not yet complete",
            )
        user.onboarding_completed_at = datetime.now(UTC).replace(tzinfo=None)
        db.commit()
        db.refresh(user)
    return _state(db, user)
