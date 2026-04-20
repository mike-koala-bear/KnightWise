# Running KnightWise locally

## Start both apps (two terminals)

Terminal 1 — web:
```bash
pnpm --filter @knightwise/web dev
# Next.js at http://localhost:3000
```

Terminal 2 — api:
```bash
uv run --directory apps/api uvicorn knightwise_api.main:app --reload --port 8000
# FastAPI at http://localhost:8000  (Swagger at /docs)
```

## Smoke-test the system
```bash
curl http://localhost:8000/healthz            # {"status":"ok"}
curl -X POST http://localhost:8000/v1/analyze \
  -H "content-type: application/json" \
  -d '{"fen":"rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1","depth":8}'
# 200 with best_move if Stockfish installed; 503 otherwise.
```

Open `http://localhost:3000` — a chessboard in the starting position should render.

## Environment
- Copy `.env.example` to `apps/api/.env` and `apps/web/.env.local`.
- `OPENAI_API_KEY` can be blank — LLM router returns stubs.
- `STOCKFISH_PATH` defaults to `/usr/local/bin/stockfish` (or whatever `which stockfish` returns).

## Ingest + analyze your own games (PR #2)

```bash
# pull latest 20 Lichess games for user `mike-bear` into SQLite
uv run --directory apps/api python -m knightwise_api.cli ingest \
  --source lichess --user mike-bear --max 20

# same thing for chess.com
uv run --directory apps/api python -m knightwise_api.cli ingest \
  --source chesscom --user mike-bear --max 20

# list what got ingested
uv run --directory apps/api python -m knightwise_api.cli games

# run Stockfish over them (depth 14 for MVP; 18–20 for prod)
uv run --directory apps/api python -m knightwise_api.cli analyze-all --depth 14 --limit 20
```

Or hit the API:
```bash
curl -X POST http://localhost:8000/v1/ingest \
  -H "content-type: application/json" \
  -d '{"source":"lichess","username":"mike-bear","max_games":20}'
curl http://localhost:8000/v1/games
curl -X POST "http://localhost:8000/v1/games/1/analyze?depth=14"
curl http://localhost:8000/v1/games/1/analysis
```

## Things that DON'T work yet (intentional, land later)
| Feature | PR |
|---|---|
| Maia-3 human-likeness tagging | #3 |
| Lesson content (MDX nodes) | #3 |
| GPT-4o-mini coach (real OpenAI calls) | #4 |
| Daily Warp composer + rating tracker | #4 |
| Branching Galaxy Path UI | #4 |
| Clerk real auth | #3 |
