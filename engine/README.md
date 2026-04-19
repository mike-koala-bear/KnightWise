# Engine

We ship KnightWise against **Stockfish 17.1** (March 2025 release, +20 Elo over SF 17).

The binary is **not committed** to this repo. Install it locally:

## macOS (Homebrew)
```bash
brew install stockfish
stockfish bench   # should run without errors
```

## Linux (apt)
```bash
sudo apt-get update && sudo apt-get install -y stockfish
```

## Manual (latest = 17.1)
Download from https://stockfishchess.org/download/ and drop the binary on `$PATH` or point `STOCKFISH_PATH` in `.env` at it.

## Verify
```bash
stockfish --version
# Stockfish 17.1 by the Stockfish developers ...
```

When the API's `/v1/analyze` endpoint is called and Stockfish is available, it uses `python-chess.engine.SimpleEngine.popen_uci` to drive the UCI protocol. From PR #2 onward we add a batch analysis pipeline that runs over every ingested game at depth 18.
