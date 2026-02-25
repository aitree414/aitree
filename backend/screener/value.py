import yfinance as yf
from .base import BaseScreener


class ValueScreener(BaseScreener):
    """Value strategy: low PE/PB, high dividend yield."""

    STRATEGY_NAME = "value"

    def screen(self, symbols: list[str]) -> list[dict]:
        results = []
        max_pe = self.thresholds.get("max_pe", 15)
        max_pb = self.thresholds.get("max_pb", 2.0)
        min_div = self.thresholds.get("min_dividend_yield", 0.03)

        for symbol in symbols:
            try:
                info = yf.Ticker(symbol).info
                pe = info.get("trailingPE") or info.get("forwardPE")
                pb = info.get("priceToBook")
                div_yield = info.get("trailingAnnualDividendYield") or 0.0
                name = info.get("longName") or info.get("shortName") or symbol

                signals = []
                score_parts = []

                if pe is not None and pe > 0 and pe < max_pe:
                    signals.append(f"PE={pe:.1f}<{max_pe}")
                    score_parts.append(1 - pe / max_pe)

                if pb is not None and pb > 0 and pb < max_pb:
                    signals.append(f"PB={pb:.2f}<{max_pb}")
                    score_parts.append(1 - pb / max_pb)

                if div_yield >= min_div:
                    signals.append(f"Div={div_yield*100:.1f}%>={min_div*100:.0f}%")
                    score_parts.append(min(div_yield / (min_div * 2), 1.0))

                if not signals:
                    continue

                score = sum(score_parts) / max(len(score_parts), 1)
                results.append({
                    "symbol": symbol,
                    "name": name,
                    "strategy": self.STRATEGY_NAME,
                    "score": round(score, 4),
                    "signals": signals,
                    "reason": f"Value: {', '.join(signals)}",
                })
            except Exception:
                continue

        return sorted(results, key=lambda x: x["score"], reverse=True)
