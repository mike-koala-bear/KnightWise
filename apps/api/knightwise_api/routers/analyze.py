from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..engine.stockfish import StockfishUnavailableError, analyze_fen

router = APIRouter(tags=["engine"])


class AnalyzeRequest(BaseModel):
    fen: str = Field(..., min_length=10)
    depth: int = Field(14, ge=1, le=30)


class AnalyzeResponse(BaseModel):
    fen: str
    depth: int
    eval_cp: int | None
    eval_mate: int | None
    best_move: str | None


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    try:
        result = analyze_fen(req.fen, depth=req.depth)
    except StockfishUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    return AnalyzeResponse(
        fen=req.fen,
        depth=req.depth,
        eval_cp=result.eval_cp,
        eval_mate=result.eval_mate,
        best_move=result.best_move,
    )
