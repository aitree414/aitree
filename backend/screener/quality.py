import math
import yfinance as yf
from .base import BaseScreener


def _log_score(value: float, minimum: float, reference_multiple: float = 10.0) -> float:
    """Log-scale score: minimum→~0.29, 10x minimum→1.0, diminishing returns beyond."""
    ratio = value / minimum
    return min(math.log1p(ratio) / math.log1p(reference_multiple), 1.0)


class QualityScreener(BaseScreener):
    """Quality strategy: high ROE, earnings growth."""

    STRATEGY_NAME = "quality"

    def screen(self, symbols: list[str]) -> list[dict]:
        results = []
        min_roe = self.thresholds.get("min_roe", 0.15)
        min_growth = self.thresholds.get("min_earnings_growth", 0.10)

        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                name = info.get("longName") or info.get("shortName") or symbol

                roe = info.get("returnOnEquity")
                earnings_growth = info.get("earningsGrowth") or info.get("earningsQuarterlyGrowth")
                revenue_growth = info.get("revenueGrowth")

                signals = []
                score_parts = []

                if roe is not None and roe >= min_roe:
                    signals.append(f"ROE={roe*100:.1f}%>={min_roe*100:.0f}%")
                    score_parts.append(_log_score(roe, min_roe))

                growth = earnings_growth or revenue_growth
                if growth is not None and growth >= min_growth:
                    signals.append(f"Growth={growth*100:.1f}%>={min_growth*100:.0f}%")
                    score_parts.append(_log_score(growth, min_growth))

                if not signals:
                    continue

                score = sum(score_parts) / max(len(score_parts), 1)
                results.append({
                    "symbol": symbol,
                    "name": name,
                    "strategy": self.STRATEGY_NAME,
                    "score": round(score, 4),
                    "signals": signals,
                    "reason": f"Quality: {', '.join(signals)}",
                })
            except Exception:
                continue

        return sorted(results, key=lambda x: x["score"], reverse=True)
