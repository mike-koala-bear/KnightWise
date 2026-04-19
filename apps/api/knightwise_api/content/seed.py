"""Load the authored lesson nodes + puzzles JSON into the DB.

Idempotent: runs may be repeated; existing rows are updated, not duplicated.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Node, NodeEdge, NodePuzzle, Puzzle

DEFAULT_SEED_PATH = Path(__file__).resolve().parents[4] / "content" / "nodes" / "seed.json"


@dataclass(slots=True)
class SeedReport:
    nodes_inserted: int = 0
    nodes_updated: int = 0
    puzzles_inserted: int = 0
    puzzles_updated: int = 0
    edges_inserted: int = 0
    node_puzzle_links_inserted: int = 0


def _upsert_node(db: Session, data: dict) -> tuple[Node, bool]:
    existing = db.execute(select(Node).where(Node.slug == data["slug"])).scalar_one_or_none()
    if existing is None:
        node = Node(
            slug=data["slug"],
            domain=data["domain"],
            title=data["title"],
            description=data.get("description"),
            rating_min=data.get("rating_min", 0),
            rating_max=data.get("rating_max", 3000),
            branch_group=data.get("branch_group"),
            content_path=data.get("content_path"),
        )
        db.add(node)
        db.flush()
        return node, True

    existing.domain = data["domain"]
    existing.title = data["title"]
    existing.description = data.get("description")
    existing.rating_min = data.get("rating_min", 0)
    existing.rating_max = data.get("rating_max", 3000)
    existing.branch_group = data.get("branch_group")
    existing.content_path = data.get("content_path")
    return existing, False


def _upsert_puzzle(db: Session, data: dict) -> tuple[Puzzle, bool]:
    existing = db.execute(
        select(Puzzle).where(Puzzle.external_id == data["external_id"])
    ).scalar_one_or_none()
    if existing is None:
        puzzle = Puzzle(
            external_id=data["external_id"],
            fen=data["fen"],
            solution_uci=list(data["solution_uci"]),
            themes=list(data.get("themes", [])),
            rating=data.get("rating", 1500),
            source=data.get("source", "knightwise"),
            description=data.get("description"),
        )
        db.add(puzzle)
        db.flush()
        return puzzle, True

    existing.fen = data["fen"]
    existing.solution_uci = list(data["solution_uci"])
    existing.themes = list(data.get("themes", []))
    existing.rating = data.get("rating", 1500)
    existing.source = data.get("source", "knightwise")
    existing.description = data.get("description")
    return existing, False


def seed_nodes_and_puzzles(db: Session, seed_path: Path | None = None) -> SeedReport:
    path = seed_path or DEFAULT_SEED_PATH
    if not path.exists():
        raise FileNotFoundError(f"Seed JSON not found: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    report = SeedReport()

    slug_to_id: dict[str, int] = {}
    for node_data in data.get("nodes", []):
        node, inserted = _upsert_node(db, node_data)
        slug_to_id[node.slug] = node.id
        if inserted:
            report.nodes_inserted += 1
        else:
            report.nodes_updated += 1

    for node_data in data.get("nodes", []):
        to_id = slug_to_id[node_data["slug"]]
        for prereq_slug in node_data.get("prereqs", []):
            from_id = slug_to_id.get(prereq_slug)
            if from_id is None:
                continue
            existing = db.execute(
                select(NodeEdge).where(
                    NodeEdge.from_node_id == from_id,
                    NodeEdge.to_node_id == to_id,
                    NodeEdge.edge_type == "prereq",
                )
            ).scalar_one_or_none()
            if existing is None:
                db.add(NodeEdge(from_node_id=from_id, to_node_id=to_id, edge_type="prereq"))
                report.edges_inserted += 1

    for puzzle_data in data.get("puzzles", []):
        puzzle, inserted = _upsert_puzzle(db, puzzle_data)
        if inserted:
            report.puzzles_inserted += 1
        else:
            report.puzzles_updated += 1

        for position, node_slug in enumerate(puzzle_data.get("nodes", [])):
            node_id = slug_to_id.get(node_slug)
            if node_id is None:
                continue
            existing_link = db.execute(
                select(NodePuzzle).where(
                    NodePuzzle.node_id == node_id, NodePuzzle.puzzle_id == puzzle.id
                )
            ).scalar_one_or_none()
            if existing_link is None:
                db.add(NodePuzzle(node_id=node_id, puzzle_id=puzzle.id, position=position))
                report.node_puzzle_links_inserted += 1

    db.commit()
    return report
