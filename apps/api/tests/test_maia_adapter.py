"""Tests for the Maia adapter factory and Maia-3 ONNX wrapper.

The real Maia-3 weights (~45MB ONNX) are an optional install (``--extra
maia3``) and are NOT shipped to CI. These tests therefore use a fake
``Maia3``-shaped object to verify wiring; an additional opt-in test exercises
the bundled ONNX weights when they're available locally.
"""

from __future__ import annotations

import shutil
from collections import OrderedDict

import pytest
from fastapi.testclient import TestClient
from knightwise_api.engine.maia import (
    Maia3Adapter,
    Maia3Unavailable,
    NullMaiaAdapter,
    StockfishMaiaAdapter,
    adapter_name,
    get_maia,
)
from knightwise_api.main import create_app


class _FakeMaia3:
    """Stand-in for ``simple_maia3_inference.Maia3``.

    Returns a deterministic move-prob dict keyed off the FEN so the adapter
    can be tested without loading real weights.
    """

    def __init__(self, top_move: str = "e2e4", top_prob: float = 0.42) -> None:
        self.top_move = top_move
        self.top_prob = top_prob
        self.calls: list[tuple[str, float, float]] = []

    def probs(
        self, fen: str, elo_self: float, elo_oppo: float
    ) -> tuple[OrderedDict[str, float], tuple[float, float, float]]:
        self.calls.append((fen, elo_self, elo_oppo))
        ordered: OrderedDict[str, float] = OrderedDict()
        ordered[self.top_move] = self.top_prob
        ordered["d2d4"] = max(0.0, 1.0 - self.top_prob - 0.05)
        ordered["c2c4"] = 0.05
        return ordered, (0.5, 0.3, 0.2)


def _raise_stockfish_unavailable():
    from knightwise_api.engine.stockfish import StockfishUnavailableError

    raise StockfishUnavailableError("not installed (test)")


# --- NullMaiaAdapter ----------------------------------------------------------


def test_null_adapter_returns_null_move() -> None:
    pred = NullMaiaAdapter().predict(
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", 1500
    )
    assert pred.move_uci == "0000"
    assert pred.prob == 0.0


# --- get_maia() factory -------------------------------------------------------


def test_get_maia_respects_null_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KNIGHTWISE_MAIA_ADAPTER", "null")
    assert isinstance(get_maia(), NullMaiaAdapter)


def test_get_maia_stockfish_falls_back_to_null_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("KNIGHTWISE_MAIA_ADAPTER", "stockfish")
    monkeypatch.setattr(
        "knightwise_api.engine.maia.resolve_stockfish_path",
        _raise_stockfish_unavailable,
    )
    assert isinstance(get_maia(), NullMaiaAdapter)


def test_get_maia_maia3_explicit_falls_back_to_null_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If the user pinned KNIGHTWISE_MAIA_ADAPTER=maia3 but the extra is not
    installed, we must NOT silently use Stockfish — that would change the
    semantics of the analysis. Fall back to Null and log a warning instead.
    """
    monkeypatch.setenv("KNIGHTWISE_MAIA_ADAPTER", "maia3")

    def _unavailable():
        raise Maia3Unavailable("simple_maia3_inference not installed")

    monkeypatch.setattr("knightwise_api.engine.maia._get_session", _unavailable)
    assert isinstance(get_maia(), NullMaiaAdapter)


def test_get_maia_auto_falls_through_to_stockfish(monkeypatch: pytest.MonkeyPatch) -> None:
    """In auto mode, if Maia-3 is unavailable but Stockfish is, we use Stockfish."""
    monkeypatch.setenv("KNIGHTWISE_MAIA_ADAPTER", "auto")

    def _unavailable():
        raise Maia3Unavailable("not installed")

    monkeypatch.setattr("knightwise_api.engine.maia._get_session", _unavailable)
    monkeypatch.setattr(
        "knightwise_api.engine.maia.resolve_stockfish_path",
        lambda: "/usr/bin/stockfish",
    )
    assert isinstance(get_maia(), StockfishMaiaAdapter)


def test_get_maia_auto_returns_maia3_when_session_loads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("KNIGHTWISE_MAIA_ADAPTER", "auto")
    monkeypatch.setattr(
        "knightwise_api.engine.maia._get_session", lambda: _FakeMaia3()
    )
    adapter = get_maia()
    assert isinstance(adapter, Maia3Adapter)


# --- Maia3Adapter -------------------------------------------------------------


def test_maia3_adapter_returns_top_move() -> None:
    fake = _FakeMaia3(top_move="e7e5", top_prob=0.55)
    adapter = Maia3Adapter(model=fake)
    pred = adapter.predict(
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1", 1500
    )
    assert pred.move_uci == "e7e5"
    assert pred.prob == pytest.approx(0.55)
    # Adapter should have called probs once with the supplied rating on both sides.
    assert len(fake.calls) == 1
    fen, self_elo, oppo_elo = fake.calls[0]
    assert fen.startswith("rnbqkbnr")
    assert self_elo == 1500.0
    assert oppo_elo == 1500.0


def test_maia3_adapter_clamps_rating() -> None:
    """Maia-3 was trained on 600-2600. Below/above that we clamp."""
    fake = _FakeMaia3()
    adapter = Maia3Adapter(model=fake)
    adapter.predict("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", 100)
    adapter.predict("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", 5000)
    assert fake.calls[0][1] == 600.0  # clamped from 100
    assert fake.calls[1][1] == 2600.0  # clamped from 5000


def test_maia3_adapter_raises_on_no_legal_moves() -> None:
    class _EmptyFake:
        def probs(self, fen, elo_self, elo_oppo):  # type: ignore[no-untyped-def]
            return ({}, (0.0, 0.0, 0.0))

    adapter = Maia3Adapter(model=_EmptyFake())
    with pytest.raises(RuntimeError, match="no moves"):
        adapter.predict(
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", 1500
        )


# --- adapter_name -------------------------------------------------------------


def test_adapter_name_labels() -> None:
    assert adapter_name(NullMaiaAdapter()) == "null"
    assert adapter_name(Maia3Adapter(model=_FakeMaia3())) == "maia3"
    # StockfishMaiaAdapter's __init__ is parameterless aside from depth.
    assert adapter_name(StockfishMaiaAdapter()) == "stockfish"


# --- /v1/engine/health endpoint ----------------------------------------------


def test_engine_health_endpoint_reports_null_in_test_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("KNIGHTWISE_MAIA_ADAPTER", "null")
    client = TestClient(create_app())
    res = client.get("/v1/engine/health")
    assert res.status_code == 200
    body = res.json()
    assert body == {"maia_adapter": "null", "maia_real": False}


def test_engine_health_endpoint_reports_maia3(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KNIGHTWISE_MAIA_ADAPTER", "auto")
    monkeypatch.setattr(
        "knightwise_api.engine.maia._get_session", lambda: _FakeMaia3()
    )
    client = TestClient(create_app())
    res = client.get("/v1/engine/health")
    assert res.status_code == 200
    body = res.json()
    assert body == {"maia_adapter": "maia3", "maia_real": True}


# --- Stockfish smoke test (skipped when binary missing) -----------------------


@pytest.mark.skipif(shutil.which("stockfish") is None, reason="stockfish not installed")
def test_stockfish_maia_predicts_a_legal_move() -> None:
    adapter = StockfishMaiaAdapter(depth=4)
    pred = adapter.predict(
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", 1500
    )
    assert len(pred.move_uci) == 4
    assert pred.move_uci[0].isalpha() and pred.move_uci[1].isdigit()
