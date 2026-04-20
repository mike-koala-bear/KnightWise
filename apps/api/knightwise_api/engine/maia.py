"""Maia-at-user-rating adapter.

Maia-3 is a single Leela-style neural net that plays 600-2600 Elo depending on a
`rating` input. Running the real net requires lc0 + weight files (not bundled here).

For the MVP we ship a pluggable protocol + a Stockfish-based approximation that uses
Stockfish's own `UCI_LimitStrength` / `UCI_Elo` options. It is *not* a true Maia
predictor (real Maia is trained on human games and captures *likely* moves, not best
rating-adjusted moves), but it provides a usable signal for the tagger until the
real Maia net is wired in (tracked as PR #5).

Callers should import `get_maia()` rather than a concrete class, so switching
implementations is a one-line env change.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol

import chess
import chess.engine

from .stockfish import StockfishUnavailableError, resolve_stockfish_path


@dataclass(slots=True)
class MaiaPrediction:
    """A single predicted move for a (fen, rating) pair.

    `prob` is a rough confidence in [0,1]; 1.0 means "this adapter is certain,"
    which for the current Stockfish approximation always is.
    """

    move_uci: str
    prob: float


class MaiaAdapter(Protocol):
    """Anything that can predict 'what would a player of rating R play here?'."""

    def predict(self, fen: str, rating: int) -> MaiaPrediction: ...


class StockfishMaiaAdapter:
    """Approximates Maia using Stockfish's built-in Elo limiter.

    Notes:
    - Stockfish clamps UCI_Elo to [1320, 3190]. We clamp inputs into that range.
    - Real Maia-3 covers 600-2600; for ratings under 1320 we fall back to a
      reduced search depth (proxies the "weak engine" effect) rather than Elo.
    - Search is deliberately shallow (depth=8) so this stays fast enough for
      per-move batch analysis over many games.
    """

    STOCKFISH_ELO_MIN = 1320
    STOCKFISH_ELO_MAX = 3190

    def __init__(self, depth: int = 8) -> None:
        self._depth = depth

    def predict(self, fen: str, rating: int) -> MaiaPrediction:
        path = resolve_stockfish_path()
        board = chess.Board(fen)

        if rating >= self.STOCKFISH_ELO_MIN:
            uci_elo = min(self.STOCKFISH_ELO_MAX, max(self.STOCKFISH_ELO_MIN, rating))
            options = {"UCI_LimitStrength": True, "UCI_Elo": uci_elo}
            depth = self._depth
        else:
            # Stockfish's UCI_Elo floor is 1320; below that we only weaken via depth.
            options = {}
            depth = max(1, min(self._depth, 2))

        with chess.engine.SimpleEngine.popen_uci(str(path)) as engine:
            for k, v in options.items():
                engine.configure({k: v})
            result = engine.play(board, chess.engine.Limit(depth=depth))

        move = result.move
        if move is None:
            raise RuntimeError(f"Engine returned no move for FEN {fen!r}")
        return MaiaPrediction(move_uci=move.uci(), prob=1.0)


class NullMaiaAdapter:
    """Used in CI and in tests when no engine is available.

    Always returns the null move "0000"; callers MUST treat the adapter being
    a `NullMaiaAdapter` (see `get_maia`) as "skip Maia-delta analysis".
    """

    def predict(self, fen: str, rating: int) -> MaiaPrediction:
        return MaiaPrediction(move_uci="0000", prob=0.0)


def get_maia() -> MaiaAdapter:
    """Adapter factory. Controlled by env var `KNIGHTWISE_MAIA_ADAPTER`.

    Values:
      - "stockfish" (default): use `StockfishMaiaAdapter` (needs stockfish binary)
      - "null":                use `NullMaiaAdapter` (no engine needed; tagger
                                skips Maia-delta logic)
    """
    choice = os.getenv("KNIGHTWISE_MAIA_ADAPTER", "stockfish").lower()
    if choice == "null":
        return NullMaiaAdapter()
    try:
        resolve_stockfish_path()
    except StockfishUnavailableError:
        return NullMaiaAdapter()
    return StockfishMaiaAdapter()


__all__ = [
    "MaiaAdapter",
    "MaiaPrediction",
    "NullMaiaAdapter",
    "StockfishMaiaAdapter",
    "get_maia",
]
