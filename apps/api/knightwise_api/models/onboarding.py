from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base


class OnboardingAttempt(Base):
    """Audit row for a single puzzle attempt during the skill test.

    These rows are append-only. The rating snapshot (`rating_mu_after`,
    `rating_sigma_after`) is captured at write time; later edits to the user's
    rating MUST NOT rewrite this history.
    """

    __tablename__ = "onboarding_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    puzzle_id: Mapped[int] = mapped_column(ForeignKey("puzzles.id"), index=True)
    correct: Mapped[bool] = mapped_column(Boolean)
    time_ms: Mapped[int] = mapped_column(Integer, default=0)
    rating_mu_after: Mapped[float] = mapped_column(Float)
    rating_sigma_after: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
