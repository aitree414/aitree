import pandas as pd
import numpy as np


def calculate_total_return(invested: float, final_value: float) -> float:
    if invested == 0:
        return 0.0
    return (final_value - invested) / invested


def calculate_cagr(invested: float, final_value: float, years: float) -> float:
    if invested <= 0 or years <= 0:
        return 0.0
    return (final_value / invested) ** (1.0 / years) - 1.0


def calculate_max_drawdown(portfolio_values: pd.Series) -> float:
    if portfolio_values.empty:
        return 0.0
    peak = portfolio_values.cummax()
    drawdown = (portfolio_values - peak) / peak
    return float(drawdown.min())


def calculate_daily_returns(prices: pd.Series) -> pd.Series:
    return prices.pct_change().dropna()


def calculate_volatility(daily_returns: pd.Series) -> float:
    if daily_returns.empty:
        return 0.0
    return float(daily_returns.std() * np.sqrt(252))


def calculate_sharpe_ratio(daily_returns: pd.Series, risk_free: float = 0.02) -> float:
    vol = calculate_volatility(daily_returns)
    if vol == 0:
        return 0.0
    annualized_return = float(daily_returns.mean() * 252)
    return (annualized_return - risk_free) / vol
