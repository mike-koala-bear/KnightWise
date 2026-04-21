import shutil

import pytest
from knightwise_api.engine.maia import NullMaiaAdapter, StockfishMaiaAdapter, get_maia


def test_null_adapter_returns_null_move():
    pred = NullMaiaAdapter().predict("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", 1500)
    assert pred.move_uci == "0000"
    assert pred.prob == 0.0


def test_get_maia_respects_null_env(monkeypatch):
    monkeypatch.setenv("KNIGHTWISE_MAIA_ADAPTER", "null")
    adapter = get_maia()
    assert isinstance(adapter, NullMaiaAdapter)


def test_get_maia_without_stockfish_falls_back_to_null(monkeypatch):
    monkeypatch.setenv("KNIGHTWISE_MAIA_ADAPTER", "stockfish")
    monkeypatch.setattr("knightwise_api.engine.maia.resolve_stockfish_path", _raise_unavailable)
    adapter = get_maia()
    assert isinstance(adapter, NullMaiaAdapter)


def _raise_unavailable():
    from knightwise_api.engine.stockfish import StockfishUnavailableError

    raise StockfishUnavailableError("not installed (test)")


@pytest.mark.skipif(shutil.which("stockfish") is None, reason="stockfish not installed")
def test_stockfish_maia_predicts_a_legal_move():
    adapter = StockfishMaiaAdapter(depth=4)
    pred = adapter.predict("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", 1500)
    # Opening move from starting position: len 4 uci, legal algebra
    assert len(pred.move_uci) == 4
    assert pred.move_uci[0].isalpha() and pred.move_uci[1].isdigit()
