"""onboarding skill test: completion timestamp + attempt audit log

Revision ID: 0002_onboarding
Revises: 0001_initial
Create Date: 2026-04-19

Adds:
- ``users.onboarding_completed_at`` so the home page can route new users into
  the skill test before any drill activity counts toward Galaxy progress.
- ``onboarding_attempts`` audit table. One row per puzzle attempt during the
  test; lets us retro-debug rating estimates and show the user the curve of
  their estimate over time.

Rating math (Glicko-1) reuses the existing ``users.rating_mu`` /
``users.rating_sigma`` columns from migration 0001 — no schema change there.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_onboarding"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("onboarding_completed_at", sa.DateTime, nullable=True))

    op.create_table(
        "onboarding_attempts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), index=True, nullable=False),
        sa.Column("puzzle_id", sa.Integer, sa.ForeignKey("puzzles.id"), index=True, nullable=False),
        sa.Column("correct", sa.Boolean, nullable=False),
        sa.Column("time_ms", sa.Integer, nullable=False, server_default="0"),
        # Snapshot of the user's Glicko estimate AFTER applying this attempt.
        # Lets the UI render the Elo curve without recomputing from scratch.
        sa.Column("rating_mu_after", sa.Float, nullable=False),
        sa.Column("rating_sigma_after", sa.Float, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("onboarding_attempts")
    with op.batch_alter_table("users") as batch:
        batch.drop_column("onboarding_completed_at")
