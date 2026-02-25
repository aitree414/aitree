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


def _build_metrics(history: list[dict], total_invested: float) -> dict:
    values = pd.Series([h["value"] for h in history])
    dates = [h["date"] for h in history]

    if values.empty or total_invested == 0:
        return {}

    final_value = float(values.iloc[-1])
    start_date = datetime.strptime(dates[0], "%Y-%m-%d")
    end_date = datetime.strptime(dates[-1], "%Y-%m-%d")
    years = max((end_date - start_date).days / 365.25, 0.001)

    daily_returns = calculate_daily_returns(values)

    return {
        "final_value": round(final_value, 2),
        "total_invested": round(total_invested, 2),
        "total_return": round(calculate_total_return(total_invested, final_value), 4),
        "cagr": round(calculate_cagr(total_invested, final_value, years), 4),
        "max_drawdown": round(calculate_max_drawdown(values), 4),
        "volatility": round(calculate_volatility(daily_returns), 4),
        "sharpe_ratio": round(calculate_sharpe_ratio(daily_returns), 4),
        "total_invested": round(total_invested, 2),
        "portfolio_history": history,
    }


def backtest_lump_sum(data: pd.DataFrame, amount: float) -> dict:
    if data.empty:
        return {}

    close = data["Close"].squeeze()
    initial_price = float(close.iloc[0])
    shares = amount / initial_price

    history = [
        {"date": str(idx.date()), "value": round(float(price) * shares, 2)}
        for idx, price in close.items()
    ]

    return _build_metrics(history, amount)


def backtest_dca(data: pd.DataFrame, monthly_amount: float, frequency: str = "monthly") -> dict:
    if data.empty:
        return {}

    close = data["Close"].squeeze()
    dates = close.index

    # Determine investment dates
    if frequency == "weekly":
        # First trading day of each week
        invest_dates = set()
        for date in dates:
            week_key = (date.year, date.isocalendar()[1])
            if week_key not in {(d.year, d.isocalendar()[1]) for d in invest_dates}:
                invest_dates.add(date)
    else:
        # Monthly: first trading day of each month
        invest_dates = set()
        seen_months = set()
        for date in dates:
            month_key = (date.year, date.month)
            if month_key not in seen_months:
                seen_months.add(month_key)
                invest_dates.add(date)

    total_shares = 0.0
    total_invested = 0.0
    history = []

    for date in dates:
        price = float(close[date])
        if date in invest_dates:
            shares_bought = monthly_amount / price
            total_shares += shares_bought
            total_invested += monthly_amount

        if total_shares > 0:
            history.append({"date": str(date.date()), "value": round(total_shares * price, 2)})

    return _build_metrics(history, total_invested)


def compare_results(results: list[dict]) -> dict:
    if not results:
        return {}

    valid = [r for r in results if r.get("total_return") is not None]
    if not valid:
        return {}

    best_return = max(valid, key=lambda r: r.get("total_return", float("-inf")))
    lowest_risk = min(valid, key=lambda r: r.get("volatility", float("inf")))
    best_sharpe = max(valid, key=lambda r: r.get("sharpe_ratio", float("-inf")))
    lowest_drawdown = min(valid, key=lambda r: r.get("max_drawdown", float("inf")))

    return {
        "best_performer": best_return.get("symbol"),
        "highest_return": best_return.get("symbol"),
        "lowest_risk": lowest_risk.get("symbol"),
        "best_sharpe": best_sharpe.get("symbol"),
        "lowest_drawdown": lowest_drawdown.get("symbol"),
    }
