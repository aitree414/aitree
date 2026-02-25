import json
import os
from datetime import datetime, date
from typing import Any

import yfinance as yf

PORTFOLIO_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "reports", "paper_portfolio.json"
)


def _load() -> dict:
    if not os.path.exists(PORTFOLIO_PATH):
        return {"positions": [], "closed": [], "strategy_stats": {}}
    with open(PORTFOLIO_PATH, "r") as f:
        return json.load(f)


def _save(data: dict) -> None:
    os.makedirs(os.path.dirname(PORTFOLIO_PATH), exist_ok=True)
    with open(PORTFOLIO_PATH, "w") as f:
        json.dump(data, f, indent=2, default=str)


class PaperPortfolio:
    """JSON-persisted paper trading tracker for strategy comparison."""

    def __init__(self):
        self._data = _load()

    def add_signal(self, symbol: str, strategy: str, entry_price: float, score: float) -> None:
        """Record a new paper trade entry signal."""
        already_open = any(
            p["symbol"] == symbol and p["strategy"] == strategy and p["status"] == "open"
            for p in self._data["positions"]
        )
        if already_open:
            return

        position = {
            "id": f"{strategy}:{symbol}:{date.today().isoformat()}",
            "symbol": symbol,
            "strategy": strategy,
            "entry_price": entry_price,
            "entry_date": date.today().isoformat(),
            "score": score,
            "status": "open",
            "current_price": entry_price,
            "pnl_pct": 0.0,
            "last_updated": datetime.now().isoformat(),
        }
        self._data["positions"].append(position)
        _save(self._data)

    def update_prices(self) -> None:
        """Fetch current prices and update P&L for all open positions."""
        open_positions = [p for p in self._data["positions"] if p["status"] == "open"]
        if not open_positions:
            return

        symbols = list({p["symbol"] for p in open_positions})
        prices: dict[str, float] = {}
        for symbol in symbols:
            try:
                fast = yf.Ticker(symbol).fast_info
                prices[symbol] = float(fast.last_price)
            except Exception:
                pass

        updated = []
        for pos in self._data["positions"]:
            if pos["status"] != "open":
                updated.append(pos)
                continue
            current = prices.get(pos["symbol"])
            if current is not None:
                pnl = (current - pos["entry_price"]) / pos["entry_price"]
                updated.append({
                    **pos,
                    "current_price": current,
                    "pnl_pct": round(pnl, 6),
                    "last_updated": datetime.now().isoformat(),
                })
            else:
                updated.append(pos)

        self._data["positions"] = updated
        self._recalculate_strategy_stats()
        _save(self._data)

    def _recalculate_strategy_stats(self) -> None:
        """Compute per-strategy win rate and average return over the last 30 days."""
        from datetime import timedelta
        cutoff = (date.today() - timedelta(days=30)).isoformat()

        strategy_results: dict[str, list[float]] = {}
        for pos in self._data["positions"]:
            if pos["entry_date"] < cutoff:
                continue
            strat = pos["strategy"]
            strategy_results.setdefault(strat, [])
            strategy_results[strat].append(pos["pnl_pct"])

        stats = {}
        for strat, returns in strategy_results.items():
            if not returns:
                continue
            wins = sum(1 for r in returns if r > 0)
            stats[strat] = {
                "count": len(returns),
                "win_rate_30d": round(wins / len(returns), 4),
                "avg_return_30d": round(sum(returns) / len(returns), 6),
                "best": round(max(returns), 6),
                "worst": round(min(returns), 6),
            }
        self._data["strategy_stats"] = stats

    def get_open_positions(self) -> list[dict]:
        return [p for p in self._data["positions"] if p["status"] == "open"]

    def get_strategy_stats(self) -> dict:
        return self._data.get("strategy_stats", {})

    def get_summary(self) -> dict[str, Any]:
        open_pos = self.get_open_positions()
        return {
            "open_positions": len(open_pos),
            "total_positions": len(self._data["positions"]),
            "strategy_stats": self.get_strategy_stats(),
            "positions": open_pos,
        }
