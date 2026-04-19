# KnightWise

Personalized, AI-driven chess learning app. Web-first. 2D branching "Galaxy Path". Stockfish 17.1 + Maia-3 + GPT-4o-mini.

See the architecture proposal for the full design. This PR lands the **Personal MVP scaffold** only — no chess analysis yet; that arrives in PR #2.

## Quickstart

Prerequisites: **Node 22+, pnpm 10+, Python 3.13, uv 0.7+**. (Stockfish 17.1 binary is required from PR #2 onward; see `engine/README.md`.)

```bash
# Install JS deps
pnpm install

# Install Python deps (uv workspace)
uv sync

# Create local SQLite DB
cd apps/api && uv run alembic upgrade head && cd ../..

# Start both apps (in two terminals)
pnpm --filter @knightwise/web dev          # Next.js at http://localhost:3000
uv run --directory apps/api uvicorn knightwise_api.main:app --reload --port 8000
```

Verify:
- `http://localhost:3000` shows a chessboard in the starting position.
- `http://localhost:8000/healthz` returns `{"status":"ok"}`.
- `http://localhost:8000/docs` renders FastAPI's Swagger UI.

## Monorepo layout

```
apps/
  web/        Next.js 16.2 + React 19.2 + Tailwind + Clerk (dev stub)
  api/        FastAPI 0.115 / Python 3.13 + SQLAlchemy 2 + Alembic
packages/
  chess/      Shared TS types and chess helpers
engine/       Stockfish binary install docs (binary NOT committed)
content/      Lesson MDX + FEN/PGN (populated in PR #3)
.agents/
  skills/     Commands for future Devin sessions
```

## Scripts

| Command | What it does |
|---|---|
| `pnpm dev` | Starts web dev server |
| `pnpm lint` | ESLint across the workspace |
| `pnpm typecheck` | TS check across the workspace |
| `pnpm test` | Vitest (added later) |
| `uv run ruff check .` | Python lint |
| `uv run pytest apps/api` | Python tests |
| `uv run alembic upgrade head` | Apply DB migrations |

## Next PRs

- **PR #2** — Lichess / Chess.com PGN ingestion + Stockfish 17.1 analysis CLI for `mike-bear`.
- **PR #3** — Maia-3 ONNX, weakness tagger, first 10 hardcoded lesson nodes, drill runtime.
- **PR #4** — Daily Warp composer, GPT-4o-mini coach, rating tracker, branching Galaxy UI v1.

## License

MIT.
