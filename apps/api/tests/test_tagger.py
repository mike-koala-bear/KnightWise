from knightwise_api.engine.analysis import MoveAnalysis
from knightwise_api.engine.maia import NullMaiaAdapter
from knightwise_api.engine.tagger import tag_game


def _m(ply: int, *, by_user: bool, classification: str, cpl: int | None, fen: str = "8/8/8/8/8/8/8/4K3 w - - 0 1", move: str = "e1e2") -> MoveAnalysis:
    return MoveAnalysis(
        ply=ply, fen_before=fen, move_uci=move, move_san="Ke2",
        best_uci=None, eval_cp_before=0, eval_cp_after=0,
        cpl=cpl, classification=classification, by_user=by_user,
    )


def test_tagger_null_adapter_still_tags_heuristics():
    per_move = [
        _m(i, by_user=True, classification="blunder" if i in (1, 3) else "good", cpl=300 if i in (1, 3) else 10)
        for i in range(1, 6)
    ]
    _, tags = tag_game(per_move, user_rating=1500, user_color="white", adapter=NullMaiaAdapter())
    assert "frequent_blunders" in tags
    assert "rating_level_mistake" not in tags  # null adapter skips maia tags


def test_tagger_back_rank_detection():
    fen_back_rank = "4k3/8/8/8/8/8/5PPP/6K1 w - - 0 1"  # white Kg1 with locked f2/g2/h2 pawns
    per_move = [
        _m(1, by_user=True, classification="blunder", cpl=300, fen=fen_back_rank, move="g1h1")
    ]
    _, tags = tag_game(per_move, user_rating=1500, user_color="white", adapter=NullMaiaAdapter())
    assert "back_rank_weakness" in tags


def test_tagger_opening_out_of_book():
    per_move = [
        _m(i, by_user=True, classification="mistake" if i <= 4 else "good", cpl=150 if i <= 4 else 10)
        for i in range(1, 12)
    ]
    _, tags = tag_game(per_move, user_rating=1500, user_color="white", adapter=NullMaiaAdapter())
    assert "opening_out_of_book" in tags
