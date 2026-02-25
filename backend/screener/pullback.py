import pandas as pd
from .base import BaseScreener
from services.data_service import get_stock_history
from .momentum import _calculate_rsi
import yfinance as yf


class PullbackScreener(BaseScreener):
    """Pullback strategy: price near MA20, RSI < 50, volume spike."""

    STRATEGY_NAME = "pullback"

    def screen(self, symbols: list[str]) -> list[dict]:
        results = []
        ma_min = self.thresholds.get("ma_proximity_min", 0.95)
        ma_max = self.thresholds.get("ma_proximity_max", 1.02)
        rsi_max = self.thresholds.get("rsi_max", 50)
        vol_mult = self.thresholds.get("volume_multiplier", 1.2)

        start, end = self._lookback_dates(60)

        for symbol in symbols:
            try:
                df = get_stock_history(symbol, start, end)
                if df.empty or len(df) < 25:
                    continue

                closes = df["Close"].squeeze()
                volumes = df["Volume"].squeeze()
                ma20 = closes.rolling(20).mean().iloc[-1]
                last_price = float(closes.iloc[-1])
                rsi = _calculate_rsi(closes)
                avg_vol = float(volumes.rolling(20).mean().iloc[-1])
                last_vol = float(volumes.iloc[-1])

                signals = []
                score_parts = []

                ratio = last_price / ma20
                if ma_min <= ratio <= ma_max:
                    signals.append(f"Price/MA20={ratio:.3f} [{ma_min}-{ma_max}]")
                    score_parts.append(1 - abs(ratio - 1.0) / 0.05)

                if rsi < rsi_max:
                    signals.append(f"RSI={rsi:.1f}<{rsi_max}")
                    score_parts.append((rsi_max - rsi) / rsi_max)

                if avg_vol > 0 and last_vol >= avg_vol * vol_mult:
                    signals.append(f"Vol={last_vol/avg_vol:.1f}x avg")
                    score_parts.append(min(last_vol / (avg_vol * vol_mult * 2), 1.0))

                if len(signals) < 2:
                    continue

                score = sum(score_parts) / max(len(score_parts), 1)
                results.append({
                    "symbol": symbol,
                    "name": symbol,
                    "strategy": self.STRATEGY_NAME,
                    "score": round(score, 4),
                    "signals": signals,
                    "reason": f"Pullback: {', '.join(signals)}",
                })
            except Exception:
                continue

        return sorted(results, key=lambda x: x["score"], reverse=True)
