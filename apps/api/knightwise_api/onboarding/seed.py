"""Load the calibrated onboarding puzzles from JSON into the puzzles table.

Idempotent: existing rows (matched by ``external_id``) are updated, never
duplicated. Onboarding puzzles live in the same ``puzzles`` table as drill
puzzles, distinguished by the ``onboarding`` theme tag.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Puzzle

DEFAULT_ONBOARDING_PATH = (
    Path(__file__).resolve().parents[4] / "content" / "nodes" / "onboarding.json"
)


@dataclass(slots=True)
class OnboardingSeedReport:
    inserted: int = 0
    updated: int = 0


def seed_onboarding_puzzles(
    db: Session, seed_path: Path | None = None
) -> OnboardingSeedReport:
    path = seed_path or DEFAULT_ONBOARDING_PATH
    if not path.exists():
        raise FileNotFoundError(f"Onboarding seed JSON not found: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    report = OnboardingSeedReport()

    for puzzle_data in data.get("puzzles", []):
        existing = db.execute(
            select(Puzzle).where(Puzzle.external_id == puzzle_data["external_id"])
        ).scalar_one_or_none()
        if existing is None:
            db.add(
                Puzzle(
                    external_id=puzzle_data["external_id"],
                    fen=puzzle_data["fen"],
                    solution_uci=list(puzzle_data["solution_uci"]),
                    themes=list(puzzle_data.get("themes", [])),
                    rating=int(puzzle_data.get("rating", 1500)),
                    source=puzzle_data.get("source", "knightwise"),
                    description=puzzle_data.get("description"),
                )
            )
            report.inserted += 1
        else:
            existing.fen = puzzle_data["fen"]
            existing.solution_uci = list(puzzle_data["solution_uci"])
            existing.themes = list(puzzle_data.get("themes", []))
            existing.rating = int(puzzle_data.get("rating", 1500))
            existing.source = puzzle_data.get("source", "knightwise")
            existing.description = puzzle_data.get("description")
            report.updated += 1

    db.commit()
    return report


__all__ = ["OnboardingSeedReport", "seed_onboarding_puzzles"]
