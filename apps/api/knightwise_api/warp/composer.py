"""Daily Warp composer.

A "Warp" is the 15-minute daily learning sequence:
  1. Pick the student's #1 weakness tag from their recent game analyses.
  2. Map that tag to the best authored lesson node.
  3. Pull N targeted drill puzzles (SM-2 due first, then unseen).
  4. Generate a GPT-4o-mini coach note explaining the weakness + today's plan.

Design goals:
  * Deterministic core (tag ranking, node mapping, drill selection) so tests
    don't depend on the LLM.
  * Graceful fallback: no games → default to `back-rank-basics` with a generic
    coach note. No puzzles for the node → skip drills, still return a warp.
  * Small, pure functions you can unit-test without a DB.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..drills.srs import next_due_puzzle_id
from ..llm.router import generate
from ..models import Game, GameAnalysis, Node, NodePuzzle, Puzzle, SrsCard

#: Ordered priority of weakness tags when multiple tie in frequency.
#: Earlier entries win ties — we favour concrete, fixable patterns over
#: diffuse ones like `frequent_mistakes`.
TAG_PRIORITY: tuple[str, ...] = (
    "back_rank_weakness",
    "missed_tactic",
    "rating_level_mistake",
    "concentration_error",
    "endgame_technique",
    "passed_pawn_technique",
    "opening_out_of_book",
    "frequent_blunders",
    "frequent_mistakes",
)

#: Map a weakness tag to the best authored lesson-node slug. Keep this in
#: sync with `content/nodes/seed.json`.
TAG_TO_NODE_SLUG: dict[str, str] = {
    "back_rank_weakness": "back-rank-basics",
    "missed_tactic": "knight-forks-basics",
    "rating_level_mistake": "double-attack",
    "concentration_error": "absolute-pins",
    "frequent_blunders": "knight-forks-basics",
    "frequent_mistakes": "absolute-pins",
    "endgame_technique": "kp-vs-k-technique",
    "passed_pawn_technique": "passed-pawn-technique",
    "opening_out_of_book": "knight-forks-basics",
}

#: Fallback node when no tags can be derived (new user, no analyzed games).
DEFAULT_NODE_SLUG = "back-rank-basics"

#: Number of drill puzzles packed into a single daily Warp.
DRILLS_PER_WARP = 8


def tag_to_node_slug(tag: str | None) -> str:
    """Pick the lesson node that best addresses a weakness tag."""
    if tag is None:
        return DEFAULT_NODE_SLUG
    return TAG_TO_NODE_SLUG.get(tag, DEFAULT_NODE_SLUG)


def rank_weakness_tags(tag_lists: list[list[str]]) -> list[tuple[str, int]]:
    """Return weakness tags ordered by (count desc, TAG_PRIORITY index asc).

    Each inner list is a single game's weakness_tags. Tags unknown to
    TAG_PRIORITY still appear, sorted after the known ones.
    """
    counts: Counter[str] = Counter()
    for tags in tag_lists:
        for tag in tags:
            counts[tag] += 1

    priority_index = {tag: i for i, tag in enumerate(TAG_PRIORITY)}

    def sort_key(item: tuple[str, int]) -> tuple[int, int, str]:
        tag, count = item
        return (-count, priority_index.get(tag, len(TAG_PRIORITY)), tag)

    return sorted(counts.items(), key=sort_key)


def _recent_tag_lists(
    db: Session, user_id: int, *, limit: int
) -> list[list[str]]:
    stmt = (
        select(GameAnalysis.weakness_tags)
        .join(Game, Game.id == GameAnalysis.game_id)
        .where(Game.user_id == user_id)
        .order_by(Game.started_at.desc())
        .limit(limit)
    )
    return [list(row or []) for (row,) in db.execute(stmt).all()]


def _select_drill_puzzle_ids(
    db: Session, user_id: int, node_id: int, *, count: int
) -> list[int]:
    """Pick `count` puzzle ids for today: SM-2-due first, then unseen in order."""
    node_puzzles = db.execute(
        select(NodePuzzle.puzzle_id)
        .where(NodePuzzle.node_id == node_id)
        .order_by(NodePuzzle.position)
    ).all()
    puzzle_ids_in_node = [pid for (pid,) in node_puzzles]
    if not puzzle_ids_in_node:
        return []

    now = datetime.utcnow()
    due_rows = db.execute(
        select(SrsCard.puzzle_id, SrsCard.due_at)
        .where(
            SrsCard.user_id == user_id,
            SrsCard.puzzle_id.in_(puzzle_ids_in_node),
            SrsCard.due_at <= now,
        )
        .order_by(SrsCard.due_at)
    ).all()
    due_ids = [pid for (pid, _) in due_rows]

    seen_stmt = select(SrsCard.puzzle_id).where(SrsCard.user_id == user_id)
    seen_ids = {row for (row,) in db.execute(seen_stmt).all()}

    selected: list[int] = []
    for pid in due_ids:
        if pid not in selected:
            selected.append(pid)
        if len(selected) >= count:
            return selected

    for pid in puzzle_ids_in_node:
        if pid in seen_ids or pid in selected:
            continue
        selected.append(pid)
        if len(selected) >= count:
            return selected

    # Last resort: use next_due_puzzle_id (same ordering as /v1/drills/next)
    while len(selected) < count:
        nxt = next_due_puzzle_id(db, user_id=user_id, node_id=node_id)
        if nxt is None or nxt in selected:
            break
        selected.append(nxt)

    return selected


def _build_coach_prompt(
    *,
    top_tag: str | None,
    tag_counts: list[tuple[str, int]],
    node_title: str,
    drill_count: int,
) -> str:
    lines = [
        "A student is starting today's 15-minute training session.",
        f"Primary weakness: {top_tag or 'unknown (new student)'}.",
    ]
    if tag_counts:
        top3 = ", ".join(f"{tag} (x{n})" for tag, n in tag_counts[:3])
        lines.append(f"Top patterns across recent games: {top3}.")
    lines.append(f"Today's lesson: {node_title}.")
    lines.append(f"Drills queued: {drill_count}.")
    lines.append(
        "Write a short coach note (2-3 sentences) for the top of their "
        "Warp page — name the weakness, explain why it costs them rating, "
        "and tell them what to look for in today's drills."
    )
    return "\n".join(lines)


@dataclass(slots=True)
class DailyWarp:
    user_id: int
    top_weakness_tag: str | None
    tag_counts: list[tuple[str, int]]
    node_id: int | None
    node_slug: str | None
    node_title: str | None
    drill_puzzle_ids: list[int]
    coach_note: str
    games_analyzed: int
    generated_at: datetime = field(default_factory=datetime.utcnow)


def compose_daily_warp(
    db: Session,
    *,
    user_id: int,
    games_window: int = 20,
    drills: int = DRILLS_PER_WARP,
) -> DailyWarp:
    """Build today's Warp for the user.

    Always returns a warp, even when the user has no games yet — falls back
    to the DEFAULT_NODE_SLUG so onboarding still has something to do.
    """
    tag_lists = _recent_tag_lists(db, user_id, limit=games_window)
    tag_counts = rank_weakness_tags(tag_lists)
    top_tag = tag_counts[0][0] if tag_counts else None

    node_slug = tag_to_node_slug(top_tag)
    node = db.execute(select(Node).where(Node.slug == node_slug)).scalar_one_or_none()

    drill_ids: list[int] = []
    if node is not None:
        drill_ids = _select_drill_puzzle_ids(db, user_id, node.id, count=drills)

    prompt = _build_coach_prompt(
        top_tag=top_tag,
        tag_counts=tag_counts,
        node_title=node.title if node else "Back-rank basics",
        drill_count=len(drill_ids),
    )
    coach_note = generate(prompt, purpose="coach_note")

    return DailyWarp(
        user_id=user_id,
        top_weakness_tag=top_tag,
        tag_counts=tag_counts,
        node_id=node.id if node else None,
        node_slug=node.slug if node else None,
        node_title=node.title if node else None,
        drill_puzzle_ids=drill_ids,
        coach_note=coach_note,
        games_analyzed=len(tag_lists),
    )


# Keep the puzzle type referenced so static analyzers don't flag the import as
# unused in future refactors; `Puzzle` is re-exported for convenience.
__all__ = [
    "DEFAULT_NODE_SLUG",
    "DRILLS_PER_WARP",
    "DailyWarp",
    "Puzzle",
    "TAG_PRIORITY",
    "TAG_TO_NODE_SLUG",
    "compose_daily_warp",
    "rank_weakness_tags",
    "tag_to_node_slug",
]
