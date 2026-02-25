import pandas as pd
import numpy as np
from datetime import datetime

from utils.calculations import (
    calculate_total_return,
    calculate_cagr,
    calculate_max_drawdown,
    calculate_daily_returns,
    calculate_volatility,
    calculate_sharpe_ratio,
)


def backtest_ma_strategy(
    data: pd.DataFrame,
    short_window: int,
    long_window: int,
    amount: float,
) -> dict:
    if data.empty:
        return {}

    close = data["Close"].squeeze().copy()
    close.name = "close"

    df = pd.DataFrame({"close": close})
    df["ma_short"] = df["close"].rolling(window=short_window).mean()
    df["ma_long"] = df["close"].rolling(window=long_window).mean()
    df = df.dropna()

    if df.empty:
        return {"error": f"Not enough data for MA({short_window},{long_window})"}

    cash = amount
    shares = 0.0
    in_position = False
    trades = []
    portfolio_history = []

    prev_short = None
    prev_long = None

    for date, row in df.iterrows():
        price = float(row["close"])
        ma_short = float(row["ma_short"])
        ma_long = float(row["ma_long"])

        # Golden cross: short crosses above long
        if prev_short is not None and prev_long is not None:
            if not in_position and prev_short <= prev_long and ma_short > ma_long:
                # Buy signal
                shares = cash / price
                cash = 0.0
                in_position = True
                trades.append({
                    "date": str(date.date()),
                    "type": "buy",
                    "price": round(price, 2),
                    "shares": round(shares, 4),
                })
            elif in_position and prev_short >= prev_long and ma_short < ma_long:
                # Death cross: sell signal
                cash = shares * price
                trades.append({
                    "date": str(date.date()),
                    "type": "sell",
                    "price": round(price, 2),
                    "shares": round(shares, 4),
                    "value": round(cash, 2),
                })
                shares = 0.0
                in_position = False

        portfolio_value = shares * price + cash
        portfolio_history.append({
            "date": str(date.date()),
            "value": round(portfolio_value, 2),
            "ma_short": round(ma_short, 4),
            "ma_long": round(ma_long, 4),
            "price": round(price, 2),
        })

        prev_short = ma_short
        prev_long = ma_long

    # Final value: liquidate if still in position
    if in_position and not df.empty:
        final_price = float(df["close"].iloc[-1])
        final_value = shares * final_price
    else:
        final_value = cash

    values = pd.Series([h["value"] for h in portfolio_history])
    dates_list = [h["date"] for h in portfolio_history]
    start_date = datetime.strptime(dates_list[0], "%Y-%m-%d")
    end_date = datetime.strptime(dates_list[-1], "%Y-%m-%d")
    years = max((end_date - start_date).days / 365.25, 0.001)

    daily_returns = calculate_daily_returns(values)

    metrics = {
        "final_value": round(final_value, 2),
        "total_invested": round(amount, 2),
        "total_return": round(calculate_total_return(amount, final_value), 4),
        "cagr": round(calculate_cagr(amount, final_value, years), 4),
        "max_drawdown": round(calculate_max_drawdown(values), 4),
        "volatility": round(calculate_volatility(daily_returns), 4),
        "sharpe_ratio": round(calculate_sharpe_ratio(daily_returns), 4),
        "num_trades": len(trades),
    }

    # Buy & Hold comparison
    bh_initial = float(close.iloc[0])
    bh_final = float(close.iloc[-1])
    bh_shares = amount / bh_initial
    bh_final_value = bh_shares * bh_final
    bh_daily = calculate_daily_returns(close)

    buy_hold_comparison = {
        "final_value": round(bh_final_value, 2),
        "total_return": round(calculate_total_return(amount, bh_final_value), 4),
        "cagr": round(calculate_cagr(amount, bh_final_value, years), 4),
        "max_drawdown": round(calculate_max_drawdown(close * bh_shares), 4),
        "volatility": round(calculate_volatility(bh_daily), 4),
        "sharpe_ratio": round(calculate_sharpe_ratio(bh_daily), 4),
    }

    return {
        "metrics": metrics,
        "portfolio_history": portfolio_history,
        "trades": trades,
        "buy_hold_comparison": buy_hold_comparison,
    }
