import json
import os
from datetime import date

import yaml
from fastapi import APIRouter, HTTPException, Query

router = APIRouter()

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "config")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "reports")


def _load_config() -> tuple[dict, list[str]]:
    with open(os.path.join(CONFIG_DIR, "thresholds.yaml")) as f:
        all_thresholds = yaml.safe_load(f)
    with open(os.path.join(CONFIG_DIR, "watchlist.json")) as f:
        watchlist = json.load(f)
    symbols = watchlist.get("us_stocks", []) + watchlist.get("tw_stocks", [])
    return all_thresholds, symbols


@router.get("/screener/run")
def run_screener(strategy: str = Query("all", description="all|value|momentum|pullback|quality")):
    """Run one or all screener strategies against the watchlist."""
    valid = {"all", "value", "momentum", "pullback", "quality"}
    if strategy not in valid:
        raise HTTPException(status_code=400, detail=f"strategy must be one of {sorted(valid)}")

    try:
        all_thresholds, symbols = _load_config()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Config load failed: {e}")

    from screener import ValueScreener, MomentumScreener, PullbackScreener, QualityScreener

    screener_map = {
        "value": ValueScreener(all_thresholds.get("value", {})),
        "momentum": MomentumScreener(all_thresholds.get("momentum", {})),
        "pullback": PullbackScreener(all_thresholds.get("pullback", {})),
        "quality": QualityScreener(all_thresholds.get("quality", {})),
    }

    if strategy == "all":
        results = {}
        for name, screener in screener_map.items():
            try:
                results[name] = screener.screen(symbols)
            except Exception as e:
                results[name] = {"error": str(e)}
        return {"date": date.today().isoformat(), "results": results}

    screener = screener_map[strategy]
    try:
        picks = screener.screen(symbols)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"date": date.today().isoformat(), "strategy": strategy, "picks": picks}


@router.get("/screener/horse-race")
def horse_race():
    """Run the full horse race (all 4 strategies in parallel) and return rankings."""
    try:
        from horse_race.runner import HorseRaceRunner
        report = HorseRaceRunner().run()
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/screener/paper-portfolio")
def paper_portfolio():
    """View current paper portfolio positions and strategy performance."""
    try:
        from horse_race.paper_portfolio import PaperPortfolio
        return PaperPortfolio().get_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/screener/report/today")
def today_report():
    """Return today's pre-generated JSON report if available."""
    report_path = os.path.join(REPORTS_DIR, f"{date.today().isoformat()}.json")
    if not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail="No report for today yet. Run the scheduler first.")
    with open(report_path) as f:
        return json.load(f)
