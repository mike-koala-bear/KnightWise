"""Glicko-1 rating update for the onboarding skill test.

Why Glicko-1 (not Glicko-2 or plain Elo):

- Plain Elo collapses uncertainty into a fixed K-factor, so a 600-rated user
  who passes a 1900 puzzle moves only ~30 points. With ~12 attempts that's
  not enough to escape the prior. We need a model where uncertainty itself
  shrinks with each measurement.
- Glicko-2 adds a volatility parameter that's only meaningful over many
  rated games (it tracks form changes over time). For a single 12-puzzle
  session it's overkill and brittle to tune.
- Glicko-1 with the standard ``q = ln(10)/400`` constants is a textbook
  Bayesian update on a Normal(mu, sigma) prior, single attempt at a time.

Treats each puzzle as a "game" against a fixed opponent (the puzzle's rating)
with sigma_opp = 0. Score is 1.0 (correct) or 0.0 (wrong) — partial credit
for slow-but-right answers is *not* modelled here on purpose: we want a clean
ability estimate, not a speed estimate.

References:
    http://www.glicko.net/glicko/glicko.pdf
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# Glicko constants. ``q = ln(10) / 400`` is the standard Elo-scale conversion.
_Q = math.log(10) / 400
_PI_SQ = math.pi**2

# Defaults used when a user has no prior measurement.
DEFAULT_MU: float = 1500.0
DEFAULT_SIGMA: float = 350.0

# Floor on sigma. Glicko's variance update can drive sigma arbitrarily low
# after many wins — capping it preserves a small amount of doubt so a single
# unlucky attempt later doesn't whiplash the estimate.
GLICKO_FLOOR_SIGMA: float = 60.0

# Above this sigma we treat the estimate as essentially un-converged. Used by
# the stopping rule: a session is "done" only when sigma falls below this.
GLICKO_CONVERGED_SIGMA: float = 80.0


@dataclass(slots=True, frozen=True)
class GlickoEstimate:
    mu: float
    sigma: float


def _g(sigma: float) -> float:
    return 1.0 / math.sqrt(1.0 + 3.0 * (_Q**2) * (sigma**2) / _PI_SQ)


def _expected(mu: float, mu_opp: float, sigma_opp: float) -> float:
    return 1.0 / (1.0 + 10.0 ** (-_g(sigma_opp) * (mu - mu_opp) / 400.0))


def update_glicko1(
    estimate: GlickoEstimate,
    *,
    opponent_rating: float,
    score: float,
    opponent_sigma: float = 0.0,
) -> GlickoEstimate:
    """Apply one Glicko-1 update.

    Args:
        estimate: Current (mu, sigma) for the player.
        opponent_rating: Rating of the puzzle.
        score: 1.0 if the player solved the puzzle, 0.0 otherwise. (No 0.5
            for slow-but-correct: see module docstring.)
        opponent_sigma: Defaults to 0 — puzzles have a known fixed rating.

    Returns:
        New (mu, sigma) post-update. Sigma is floored at
        :data:`GLICKO_FLOOR_SIGMA`.
    """
    if score not in (0.0, 1.0):
        raise ValueError(f"score must be 0.0 or 1.0, got {score!r}")

    g = _g(opponent_sigma)
    e = _expected(estimate.mu, opponent_rating, opponent_sigma)
    # d² is the variance of the player's expected performance given current sigma.
    d_sq = 1.0 / ((_Q**2) * (g**2) * e * (1.0 - e))

    inv_var = 1.0 / (estimate.sigma**2) + 1.0 / d_sq
    new_sigma = math.sqrt(1.0 / inv_var)
    new_mu = estimate.mu + (_Q / inv_var) * g * (score - e)

    return GlickoEstimate(mu=new_mu, sigma=max(GLICKO_FLOOR_SIGMA, new_sigma))


__all__ = [
    "DEFAULT_MU",
    "DEFAULT_SIGMA",
    "GLICKO_CONVERGED_SIGMA",
    "GLICKO_FLOOR_SIGMA",
    "GlickoEstimate",
    "update_glicko1",
]
