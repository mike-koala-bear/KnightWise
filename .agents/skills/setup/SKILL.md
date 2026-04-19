# Setting up KnightWise locally

## Prerequisites
- Node 22+
- pnpm 10+ (`corepack enable && corepack use pnpm@10.15.0`)
- Python 3.13 (`uv python install 3.13`)
- uv 0.7+
- Stockfish 17.1 (optional for PR #1; required from PR #2)

## First-time install
```bash
pnpm install
uv sync --all-extras
cd apps/api && uv run alembic upgrade head && cd ../..
```

## If install fails
- **pnpm lockfile drift**: re-run `pnpm install` (no `--frozen-lockfile`). A lockfile is committed but deps may update.
- **Python 3.13 missing**: `uv python install 3.13` then retry `uv sync`.
- **Alembic errors on SQLite**: ensure `apps/api/knightwise.db` isn't locked by another process; delete it and re-run `alembic upgrade head`.

## Verify install
```bash
pnpm --filter @knightwise/web typecheck
pnpm --filter @knightwise/web lint
uv run ruff check .
uv run pytest apps/api -v
```
All four should pass with zero errors.
