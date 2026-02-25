import pandas as pd
from .base import BaseScreener
from services.data_service import get_stock_history
import yfinance as yf


def _calculate_rsi(prices: pd.Series, period: int = 14) -> float:
    delta = prices.diff().dropna()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean().iloc[-1]
    avg_loss = loss.rolling(period).mean().iloc[-1]
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - 100 / (1 + rs), 2)


def _calculate_macd(prices: pd.Series) -> tuple[float, float]:
    ema12 = prices.ewm(span=12, adjust=False).mean()
    ema26 = prices.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    return float(macd.iloc[-1]), float(signal.iloc[-1])


class MomentumScreener(BaseScreener):
    """Momentum strategy: MA crossover, RSI 50-70, MACD > Signal."""

    STRATEGY_NAME = "momentum"

    def screen(self, symbols: list[str]) -> list[dict]:
        results = []
        rsi_min = self.thresholds.get("rsi_min", 50)
        rsi_max = self.thresholds.get("rsi_max", 70)
        lookback = self.thresholds.get("lookback_days", 60)

        start, end = self._lookback_dates(lookback + 30)

        for symbol in symbols:
            try:
                df = get_stock_history(symbol, start, end)
                if df.empty or len(df) < 26:
                    continue

                closes = df["Close"].squeeze()
                ma5 = closes.rolling(5).mean().iloc[-1]
                ma20 = closes.rolling(20).mean().iloc[-1]
                rsi = _calculate_rsi(closes)
                macd_val, macd_signal = _calculate_macd(closes)

                signals = []
                score_parts = []

                if ma5 > ma20:
                    signals.append(f"MA5({ma5:.2f})>MA20({ma20:.2f})")
                    score_parts.append(min((ma5 - ma20) / ma20 * 10, 1.0))

                if rsi_min <= rsi <= rsi_max:
                    signals.append(f"RSI={rsi:.1f} [{rsi_min}-{rsi_max}]")
                    midpoint = (rsi_min + rsi_max) / 2
                    score_parts.append(1 - abs(rsi - midpoint) / (midpoint - rsi_min))

                if macd_val > macd_signal:
                    signals.append(f"MACD({macd_val:.3f})>Signal({macd_signal:.3f})")
                    score_parts.append(min((macd_val - macd_signal) / max(abs(macd_signal), 0.001), 1.0))

                if not signals:
                    continue

                info = yf.Ticker(symbol).fast_info
                name = symbol

                score = sum(score_parts) / max(len(score_parts), 1)
                results.append({
                    "symbol": symbol,
                    "name": name,
                    "strategy": self.STRATEGY_NAME,
                    "score": round(score, 4),
                    "signals": signals,
                    "reason": f"Momentum: {', '.join(signals)}",
                })
            except Exception:
                continue

        return sorted(results, key=lambda x: x["score"], reverse=True)
