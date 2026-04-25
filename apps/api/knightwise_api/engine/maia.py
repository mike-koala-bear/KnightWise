"""Maia-at-user-rating adapter.

Maia-3 is a single neural net that predicts what a *human* of a given rating
is most likely to play in a position. Unlike Stockfish, which always returns
the best move (optionally weakened), Maia-3 captures the systematic mistakes
humans make at each rating level. That signal is exactly what the weakness
tagger needs: "did the user play the move a 1500 player would play, and is
that move bad?" → rating-level mistake.

Three concrete adapters ship here, in priority order:

1. ``Maia3Adapter``         — real Maia-3 ONNX inference via the optional
                              ``simple_maia3_inference`` package. Requires the
                              ``maia3`` extra (``uv sync --extra maia3``).
2. ``StockfishMaiaAdapter`` — Stockfish with ``UCI_LimitStrength`` /
                              ``UCI_Elo``. Cheap fallback. Captures *strength*
                              but NOT *human-likeness*, so the tagger gets a
                              weaker signal.
3. ``NullMaiaAdapter``      — used in CI / tests / when nothing else is
                              available. The tagger detects this and skips
                              all Maia-delta logic.

Callers should import :func:`get_maia` rather than a concrete class so the
adapter can be swapped via ``KNIGHTWISE_MAIA_ADAPTER``.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

import chess
import chess.engine

from .stockfish import StockfishUnavailableError, resolve_stockfish_path

if TYPE_CHECKING:
    from simple_maia3_inference import Maia3 as _Maia3Type
else:
    _Maia3Type = Any

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class MaiaPrediction:
    """A single predicted move for a (fen, rating) pair.

    ``prob`` is the model's confidence in the predicted move, in [0, 1].
    For the Stockfish-Elo approximation it is always 1.0 (no distribution).
    """

    move_uci: str
    prob: float


class MaiaAdapter(Protocol):
    """Anything that can predict 'what would a player of rating R play here?'."""

    def predict(self, fen: str, rating: int) -> MaiaPrediction: ...


class Maia3Adapter:
    """Real Maia-3 ONNX inference.

    Loads the bundled ONNX weights from the optional ``simple_maia3_inference``
    package and runs CPU inference per call. The session is cached process-wide
    via :func:`_get_session` because cold-start is ~3-5s for a 45MB model.

    Notes:
    - Maia-3 takes both ``elo_self`` and ``elo_oppo``. We treat the position
      as self-vs-self at the supplied rating; this matches how the tagger uses
      the prediction (asking "what would a peer play here?").
    - Maia-3 was trained on Lichess 600-2600 rapid/blitz. Inputs outside that
      range are clamped.
    """

    MIN_RATING = 600
    MAX_RATING = 2600

    def __init__(self, model: _Maia3Type | None = None) -> None:
        # Tests inject a fake; production callers go through get_maia().
        self._model = model

    def _resolve_model(self) -> _Maia3Type:
        if self._model is not None:
            return self._model
        self._model = _get_session()
        return self._model

    def predict(self, fen: str, rating: int) -> MaiaPrediction:
        model = self._resolve_model()
        clamped = max(self.MIN_RATING, min(self.MAX_RATING, rating))
        move_probs, _ldw = model.probs(
            fen=fen, elo_self=float(clamped), elo_oppo=float(clamped)
        )
        if not move_probs:
            # No legal moves (terminal position). Match the StockfishMaiaAdapter
            # contract — caller treats RuntimeError as "skip this position".
            raise RuntimeError(f"Maia-3 returned no moves for FEN {fen!r}")
        # move_probs is already sorted descending by probability.
        top_uci, top_prob = next(iter(move_probs.items()))
        return MaiaPrediction(move_uci=top_uci, prob=float(top_prob))


_CACHED_MAIA3: _Maia3Type | None = None


def _get_session() -> _Maia3Type:
    """Lazy-load the Maia-3 ONNX session and cache it per process.

    Raises :class:`Maia3Unavailable` if the optional dependency is missing or
    the ONNX runtime cannot be initialised. Callers (specifically
    :func:`get_maia`) MUST handle that exception and fall back.
    """
    global _CACHED_MAIA3
    if _CACHED_MAIA3 is not None:
        return _CACHED_MAIA3
    try:
        from simple_maia3_inference import Maia3
    except ImportError as exc:  # pragma: no cover - import-failure path
        raise Maia3UnavailableError("simple_maia3_inference is not installed") from exc
    try:
        _CACHED_MAIA3 = Maia3(providers=["CPUExecutionProvider"])
    except Exception as exc:  # pragma: no cover - runtime init failure
        raise Maia3UnavailableError(f"failed to load Maia-3 ONNX session: {exc}") from exc
    return _CACHED_MAIA3


class Maia3UnavailableError(RuntimeError):
    """Raised when Maia-3 cannot be loaded (missing extra or runtime error)."""


# Backwards-compat alias for older imports; prefer Maia3UnavailableError.
Maia3Unavailable = Maia3UnavailableError


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


_ADAPTER_NAME_AUTO = "auto"
_ADAPTER_NAME_MAIA3 = "maia3"
_ADAPTER_NAME_STOCKFISH = "stockfish"
_ADAPTER_NAME_NULL = "null"


def adapter_name(adapter: MaiaAdapter) -> str:
    """Return a stable string label for ``adapter``. Used by the health endpoint."""
    if isinstance(adapter, Maia3Adapter):
        return _ADAPTER_NAME_MAIA3
    if isinstance(adapter, StockfishMaiaAdapter):
        return _ADAPTER_NAME_STOCKFISH
    if isinstance(adapter, NullMaiaAdapter):
        return _ADAPTER_NAME_NULL
    return type(adapter).__name__


def get_maia() -> MaiaAdapter:
    """Adapter factory. Controlled by env var ``KNIGHTWISE_MAIA_ADAPTER``.

    Values:
      - ``"auto"`` (default): try Maia-3 → Stockfish → Null.
      - ``"maia3"``:  hard-require real Maia-3. Falls back to Null on failure.
      - ``"stockfish"``: skip Maia-3 even if available; use Stockfish-Elo only.
      - ``"null"``: no engine. Tagger skips all Maia-delta logic.
    """
    choice = os.getenv("KNIGHTWISE_MAIA_ADAPTER", _ADAPTER_NAME_AUTO).lower()

    if choice == _ADAPTER_NAME_NULL:
        return NullMaiaAdapter()

    if choice in (_ADAPTER_NAME_AUTO, _ADAPTER_NAME_MAIA3):
        try:
            _get_session()
        except Maia3UnavailableError as exc:
            if choice == _ADAPTER_NAME_MAIA3:
                logger.warning(
                    "KNIGHTWISE_MAIA_ADAPTER=maia3 requested but unavailable (%s); "
                    "falling back to NullMaiaAdapter",
                    exc,
                )
                return NullMaiaAdapter()
            logger.info("Maia-3 unavailable (%s); falling back to Stockfish-Elo", exc)
        else:
            return Maia3Adapter()

    # Stockfish path (explicit choice OR auto-fallback when Maia-3 missing).
    try:
        resolve_stockfish_path()
    except StockfishUnavailableError:
        return NullMaiaAdapter()
    return StockfishMaiaAdapter()


__all__ = [
    "Maia3Adapter",
    "Maia3Unavailable",
    "Maia3UnavailableError",
    "MaiaAdapter",
    "MaiaPrediction",
    "NullMaiaAdapter",
    "StockfishMaiaAdapter",
    "adapter_name",
    "get_maia",
]
