"""Unit tests for the Glicko-1 update + selector + stopping rule."""

from __future__ import annotations

from knightwise_api.onboarding import (
    DEFAULT_MU,
    DEFAULT_SIGMA,
    GLICKO_FLOOR_SIGMA,
    GlickoEstimate,
    is_session_complete,
    pick_next_puzzle,
    update_glicko1,
)
from knightwise_api.onboarding.selector import MAX_ATTEMPTS, MIN_ATTEMPTS, Candidate


def test_default_estimate_starts_at_1500_350() -> None:
    assert DEFAULT_MU == 1500.0
    assert DEFAULT_SIGMA == 350.0


def test_correct_at_higher_puzzle_raises_mu_lowers_sigma() -> None:
    start = GlickoEstimate(mu=1500.0, sigma=350.0)
    after = update_glicko1(start, opponent_rating=1800.0, score=1.0)
    assert after.mu > start.mu
    assert after.sigma < start.sigma


def test_wrong_at_lower_puzzle_lowers_mu() -> None:
    start = GlickoEstimate(mu=1500.0, sigma=350.0)
    after = update_glicko1(start, opponent_rating=1200.0, score=0.0)
    assert after.mu < start.mu
    assert after.sigma < start.sigma


def test_correct_at_much_lower_puzzle_barely_moves_mu() -> None:
    """A 1500 user solving an 800 puzzle should not jump to 1700: the result
    was already expected, so the update is small."""
    start = GlickoEstimate(mu=1500.0, sigma=350.0)
    after = update_glicko1(start, opponent_rating=800.0, score=1.0)
    assert after.mu - start.mu < 30


def test_score_must_be_zero_or_one() -> None:
    import pytest

    with pytest.raises(ValueError):
        update_glicko1(GlickoEstimate(1500, 350), opponent_rating=1500, score=0.5)


def test_sigma_floor_holds_after_many_wins() -> None:
    """Glicko's variance keeps shrinking but we floor it for stability."""
    est = GlickoEstimate(mu=1500.0, sigma=350.0)
    for _ in range(50):
        est = update_glicko1(est, opponent_rating=1500.0, score=1.0)
    assert est.sigma >= GLICKO_FLOOR_SIGMA


def test_pick_next_puzzle_picks_nearest_unseen() -> None:
    pool = [Candidate(1, 800), Candidate(2, 1500), Candidate(3, 2200)]
    chosen = pick_next_puzzle(pool, estimate=GlickoEstimate(1500, 200))
    assert chosen is not None and chosen.id == 2


def test_pick_next_puzzle_skips_seen() -> None:
    pool = [Candidate(1, 800), Candidate(2, 1500), Candidate(3, 2200)]
    chosen = pick_next_puzzle(
        pool, estimate=GlickoEstimate(1500, 200), seen_puzzle_ids=[2]
    )
    assert chosen is not None and chosen.id in (1, 3)


def test_pick_next_puzzle_returns_none_when_pool_exhausted() -> None:
    pool = [Candidate(1, 800), Candidate(2, 1500)]
    chosen = pick_next_puzzle(
        pool, estimate=GlickoEstimate(1500, 200), seen_puzzle_ids=[1, 2]
    )
    assert chosen is None


def test_session_complete_after_max_attempts() -> None:
    assert is_session_complete(
        attempts_so_far=MAX_ATTEMPTS, estimate=GlickoEstimate(1500, 200)
    )


def test_session_not_complete_below_min_even_if_converged() -> None:
    assert not is_session_complete(
        attempts_so_far=MIN_ATTEMPTS - 1, estimate=GlickoEstimate(1500, 50)
    )


def test_session_complete_when_min_reached_and_sigma_converged() -> None:
    assert is_session_complete(
        attempts_so_far=MIN_ATTEMPTS, estimate=GlickoEstimate(1500, 75)
    )
