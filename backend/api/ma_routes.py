from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.data_service import get_stock_history, get_stock_price
from services.ma_service import backtest_ma_strategy

router = APIRouter()


class MABacktestRequest(BaseModel):
    symbol: str
    start_date: str
    end_date: str
    short_window: int = 20
    long_window: int = 60
    amount: float = 100000


@router.post("/ma-backtest")
def run_ma_backtest(req: MABacktestRequest):
    if req.short_window >= req.long_window:
        raise HTTPException(status_code=400, detail="short_window must be less than long_window")
    if req.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    try:
        data = get_stock_history(req.symbol, req.start_date, req.end_date)
        if data.empty:
            raise HTTPException(status_code=404, detail=f"No data for {req.symbol}")

        result = backtest_ma_strategy(data, req.short_window, req.long_window, req.amount)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        price_info = get_stock_price(req.symbol)
        result["symbol"] = req.symbol
        result["name"] = price_info.get("name", req.symbol)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
