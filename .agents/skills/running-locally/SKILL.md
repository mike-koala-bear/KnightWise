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

## Things that DON'T work yet (intentional, land later)
| Feature | PR |
|---|---|
| Lichess/Chess.com PGN ingestion | #2 |
| Real engine batch analysis + weakness tagger | #2 |
| Maia-3 human-likeness tagging | #3 |
| Lesson content (MDX nodes) | #3 |
| GPT-4o-mini coach (real OpenAI calls) | #4 |
| Daily Warp composer + rating tracker | #4 |
| Branching Galaxy Path UI | #4 |
| Clerk real auth | #3 |
