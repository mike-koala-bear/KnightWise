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

## Optional: Maia-3 ONNX engine (~50MB)
Maia-3 is a real human-trained neural net used by the weakness tagger. Without
it the API falls back to Stockfish-Elo (worse human-likeness signal) or
NullMaiaAdapter (no Maia-delta tags at all).

```bash
# from repo root
cd apps/api
uv sync --extra maia3
uv run python -m knightwise_api.cli maia-check  # smoke-test
```

`maia-check` should print `active adapter: maia3` and top-3 predicted moves.
If it says `null`, set `KNIGHTWISE_MAIA_ADAPTER=auto` (default already), or
explicitly `KNIGHTWISE_MAIA_ADAPTER=maia3` to require Maia-3 (will fall back to
Null if the extra isn't installed).

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
