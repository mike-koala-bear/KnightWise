from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base


class Puzzle(Base):
    __tablename__ = "puzzles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[str | None] = mapped_column(String, nullable=True, unique=True)
    fen: Mapped[str] = mapped_column(String(128), index=True)
    solution_uci: Mapped[list[str]] = mapped_column(JSON, default=list)
    themes: Mapped[list[str]] = mapped_column(JSON, default=list)
    rating: Mapped[int] = mapped_column(Integer, default=1500)
    source: Mapped[str] = mapped_column(String(32), default="lichess")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class NodePuzzle(Base):
    __tablename__ = "node_puzzles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    node_id: Mapped[int] = mapped_column(ForeignKey("nodes.id"), index=True)
    puzzle_id: Mapped[int] = mapped_column(ForeignKey("puzzles.id"), index=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
