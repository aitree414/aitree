from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from services.data_service import search_stocks, get_stock_history, get_stock_price
from services.backtest_service import backtest_lump_sum, backtest_dca, compare_results

router = APIRouter()


class BacktestRequest(BaseModel):
    stocks: list[str]
    start_date: str
    end_date: str
    strategy: str = "lump_sum"
    amount: float = 100000
    frequency: Optional[str] = "monthly"


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/stocks/search")
def stock_search(q: str = Query(..., min_length=1)):
    try:
        results = search_stocks(q)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stocks/{symbol}")
def stock_info(symbol: str):
    try:
        data = get_stock_price(symbol)
        if data.get("error"):
            raise HTTPException(status_code=404, detail=data["error"])
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backtest")
def run_backtest(req: BacktestRequest):
    if not req.stocks:
        raise HTTPException(status_code=400, detail="At least one stock required")
    if req.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    if req.strategy not in ("lump_sum", "dca"):
        raise HTTPException(status_code=400, detail="Strategy must be lump_sum or dca")

    results = []
    for symbol in req.stocks:
        try:
            data = get_stock_history(symbol, req.start_date, req.end_date)
            if data.empty:
                results.append({"symbol": symbol, "error": "No data available"})
                continue

            price_info = get_stock_price(symbol)
            name = price_info.get("name", symbol)

            if req.strategy == "lump_sum":
                metrics = backtest_lump_sum(data, req.amount)
            else:
                metrics = backtest_dca(data, req.amount, req.frequency or "monthly")

            if not metrics:
                results.append({"symbol": symbol, "error": "Calculation failed"})
                continue

            metrics["symbol"] = symbol
            metrics["name"] = name
            results.append(metrics)
        except Exception as e:
            results.append({"symbol": symbol, "error": str(e)})

    valid_results = [r for r in results if "error" not in r]
    comparison = compare_results(valid_results) if len(valid_results) > 1 else {}

    return {"results": results, "comparison": comparison}
