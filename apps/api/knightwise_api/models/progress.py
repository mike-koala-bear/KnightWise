from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base


class NodeProgress(Base):
    __tablename__ = "node_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    node_id: Mapped[int] = mapped_column(ForeignKey("nodes.id"), index=True)
    status: Mapped[str] = mapped_column(String(16), default="locked")
    # "locked" | "available" | "in_progress" | "completed"
    mastery: Mapped[float] = mapped_column(Float, default=0.0)  # 0..1
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class PuzzleAttempt(Base):
    __tablename__ = "puzzle_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    puzzle_id: Mapped[int] = mapped_column(ForeignKey("puzzles.id"), index=True)
    node_id: Mapped[int | None] = mapped_column(ForeignKey("nodes.id"), nullable=True)
    correct: Mapped[bool] = mapped_column(Boolean)
    time_ms: Mapped[int] = mapped_column(Integer)
    hints_used: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class SrsCard(Base):
    """SM-2 for PR #1; upgrade to FSRS v6 fields in PR #3."""

    __tablename__ = "srs_cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    puzzle_id: Mapped[int] = mapped_column(ForeignKey("puzzles.id"), index=True)
    ease: Mapped[float] = mapped_column(Float, default=2.5)
    interval_days: Mapped[int] = mapped_column(Integer, default=0)
    repetitions: Mapped[int] = mapped_column(Integer, default=0)
    due_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
    # FSRS v6 fields (unused in PR #1 but declared for forward compat)
    stability: Mapped[float | None] = mapped_column(Float, nullable=True)
    difficulty: Mapped[float | None] = mapped_column(Float, nullable=True)
    decay: Mapped[float | None] = mapped_column(Float, nullable=True, default=-0.5)
