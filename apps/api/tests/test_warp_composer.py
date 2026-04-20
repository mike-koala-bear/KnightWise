from datetime import datetime, timedelta

from knightwise_api.content import seed_nodes_and_puzzles
from knightwise_api.models import Game, GameAnalysis, User
from knightwise_api.warp import compose_daily_warp, tag_to_node_slug
from knightwise_api.warp.composer import rank_weakness_tags


def _make_user(db, user_id: int = 1) -> User:
    user = User(id=user_id, display_name=f"user-{user_id}")
    db.add(user)
    db.commit()
    return user


def _add_analyzed_game(
    db,
    *,
    user_id: int,
    weakness_tags: list[str],
    started_at: datetime,
    user_rating: int | None = 1200,
) -> None:
    game = Game(
        user_id=user_id,
        source="lichess",
        external_id=f"g{started_at.isoformat()}",
        played_as="white",
        result="loss",
        pgn="1. e4 e5",
        started_at=started_at,
        user_rating=user_rating,
    )
    db.add(game)
    db.flush()
    analysis = GameAnalysis(
        game_id=game.id,
        engine="stockfish-17.1",
        depth=14,
        per_move=[],
        weakness_tags=weakness_tags,
        cpl_avg=40.0,
    )
    db.add(analysis)
    db.commit()


def test_rank_tags_counts_and_priority():
    ranked = rank_weakness_tags(
        [
            ["back_rank_weakness", "frequent_mistakes"],
            ["back_rank_weakness", "missed_tactic"],
            ["missed_tactic"],
        ]
    )
    # counts: back_rank_weakness=2, missed_tactic=2, frequent_mistakes=1
    # tie-break: back_rank_weakness has higher priority index (0) than missed_tactic (1)
    assert ranked[0][0] == "back_rank_weakness"
    assert ranked[1][0] == "missed_tactic"
    assert ranked[-1][0] == "frequent_mistakes"


def test_rank_tags_empty():
    assert rank_weakness_tags([]) == []
    assert rank_weakness_tags([[], []]) == []


def test_tag_to_node_mapping():
    assert tag_to_node_slug("back_rank_weakness") == "back-rank-basics"
    assert tag_to_node_slug("endgame_technique") == "kp-vs-k-technique"
    assert tag_to_node_slug(None) == "back-rank-basics"
    assert tag_to_node_slug("unknown-tag") == "back-rank-basics"


def test_compose_warp_no_games_returns_default(db_session):
    seed_nodes_and_puzzles(db_session)
    _make_user(db_session)
    warp = compose_daily_warp(db_session, user_id=1)
    assert warp.top_weakness_tag is None
    assert warp.node_slug == "back-rank-basics"
    assert warp.games_analyzed == 0
    assert len(warp.drill_puzzle_ids) >= 1


def test_compose_warp_picks_top_weakness(db_session):
    seed_nodes_and_puzzles(db_session)
    _make_user(db_session)
    now = datetime.utcnow()
    _add_analyzed_game(
        db_session,
        user_id=1,
        weakness_tags=["back_rank_weakness", "missed_tactic"],
        started_at=now - timedelta(days=1),
    )
    _add_analyzed_game(
        db_session,
        user_id=1,
        weakness_tags=["endgame_technique"],
        started_at=now - timedelta(days=2),
    )
    _add_analyzed_game(
        db_session,
        user_id=1,
        weakness_tags=["endgame_technique", "passed_pawn_technique"],
        started_at=now - timedelta(days=3),
    )
    warp = compose_daily_warp(db_session, user_id=1)
    assert warp.top_weakness_tag == "endgame_technique"
    assert warp.node_slug == "kp-vs-k-technique"
    assert warp.games_analyzed == 3
    assert warp.coach_note  # stub or real, must be non-empty


def test_compose_warp_respects_drill_count(db_session):
    seed_nodes_and_puzzles(db_session)
    _make_user(db_session)
    warp = compose_daily_warp(db_session, user_id=1, drills=1)
    assert len(warp.drill_puzzle_ids) == 1
