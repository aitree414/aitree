from __future__ import annotations

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from typing import Any, Optional

import yaml

# Allow imports from backend root when run as script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from screener import ValueScreener, MomentumScreener, PullbackScreener, QualityScreener
from horse_race.paper_portfolio import PaperPortfolio
import yfinance as yf

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "config")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "reports")


def _load_config() -> tuple[dict, list[str]]:
    thresholds_path = os.path.join(CONFIG_DIR, "thresholds.yaml")
    watchlist_path = os.path.join(CONFIG_DIR, "watchlist.json")

    with open(thresholds_path) as f:
        all_thresholds = yaml.safe_load(f)

    with open(watchlist_path) as f:
        watchlist = json.load(f)

    symbols = watchlist.get("us_stocks", []) + watchlist.get("tw_stocks", [])
    return all_thresholds, symbols


def _get_entry_price(symbol: str) -> float:
    try:
        return float(yf.Ticker(symbol).fast_info.last_price or 0)
    except Exception:
        return 0.0


def _run_strategy(screener, symbols: list[str]) -> list[dict]:
    return screener.screen(symbols)


class HorseRaceRunner:
    """Run all 4 screener strategies in parallel and aggregate rankings."""

    def run(self, symbols: Optional[list[str]] = None) -> dict[str, Any]:
        all_thresholds, default_symbols = _load_config()
        symbols = symbols or default_symbols

        screeners = {
            "value": ValueScreener(all_thresholds.get("value", {})),
            "momentum": MomentumScreener(all_thresholds.get("momentum", {})),
            "pullback": PullbackScreener(all_thresholds.get("pullback", {})),
            "quality": QualityScreener(all_thresholds.get("quality", {})),
        }

        strategy_results: dict[str, list[dict]] = {}
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(_run_strategy, screener, symbols): name
                for name, screener in screeners.items()
            }
            for future in as_completed(futures):
                name = futures[future]
                try:
                    strategy_results[name] = future.result()
                except Exception as e:
                    strategy_results[name] = []

        # Record paper trades for top 5 picks of each strategy
        portfolio = PaperPortfolio()
        for strategy_name, picks in strategy_results.items():
            for pick in picks[:5]:
                price = _get_entry_price(pick["symbol"])
                if price > 0:
                    portfolio.add_signal(
                        pick["symbol"], strategy_name, price, pick["score"]
                    )

        # Update P&L for existing open positions
        portfolio.update_prices()
        stats = portfolio.get_strategy_stats()

        # Build leaderboard: blend score rank with historical win rate
        leaderboard = []
        for strategy_name, picks in strategy_results.items():
            top = picks[:10]
            hist = stats.get(strategy_name, {})
            leaderboard.append({
                "strategy": strategy_name,
                "top_picks": top,
                "pick_count": len(picks),
                "win_rate_30d": hist.get("win_rate_30d"),
                "avg_return_30d": hist.get("avg_return_30d"),
                "count_30d": hist.get("count"),
            })

        # Sort leaderboard by win_rate_30d (None last)
        leaderboard.sort(
            key=lambda x: (x["win_rate_30d"] is not None, x["win_rate_30d"] or 0),
            reverse=True,
        )

        report = {
            "date": date.today().isoformat(),
            "leaderboard": leaderboard,
            "portfolio_summary": portfolio.get_summary(),
        }

        # Persist daily report
        os.makedirs(REPORTS_DIR, exist_ok=True)
        report_path = os.path.join(REPORTS_DIR, f"{date.today().isoformat()}.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

        return report
