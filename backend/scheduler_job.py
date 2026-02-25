"""
Zero-token daily investment horse race scheduler.

Usage:
    python3 scheduler_job.py          # Daemon mode: run every day at 08:30
    python3 scheduler_job.py --now    # Run once immediately and exit
"""
import json
import os
import sys
import logging
from datetime import date

# Allow imports from this directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load .env from project root
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")


def _notify_telegram(report: dict) -> None:
    """Send top 3 picks from each strategy to Telegram bot if configured."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        logger.info("Telegram credentials not set, skipping notification.")
        return

    try:
        import httpx

        lines = [f"Daily Horse Race — {report['date']}\n"]
        for entry in report.get("leaderboard", [])[:4]:
            strat = entry["strategy"].upper()
            wr = entry.get("win_rate_30d")
            wr_str = f"{wr*100:.0f}%" if wr is not None else "N/A"
            picks = [p["symbol"] for p in entry.get("top_picks", [])[:3]]
            lines.append(f"[{strat}] WR={wr_str}  Top: {', '.join(picks)}")

        message = "\n".join(lines)
        httpx.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message},
            timeout=10,
        )
        logger.info("Telegram notification sent.")
    except Exception as e:
        logger.warning(f"Telegram notification failed: {e}")


def run_daily_job() -> None:
    logger.info("Starting daily horse race scan...")
    try:
        from horse_race.runner import HorseRaceRunner
        report = HorseRaceRunner().run()

        report_path = os.path.join(REPORTS_DIR, f"{date.today().isoformat()}.json")
        logger.info(f"Report saved: {report_path}")

        # Log leaderboard summary
        for entry in report.get("leaderboard", []):
            strat = entry["strategy"]
            count = entry["pick_count"]
            wr = entry.get("win_rate_30d")
            wr_str = f"{wr*100:.0f}%" if wr is not None else "N/A"
            logger.info(f"  {strat}: {count} picks, 30d WR={wr_str}")

        _notify_telegram(report)
        logger.info("Daily job complete.")
    except Exception as e:
        logger.error(f"Daily job failed: {e}", exc_info=True)


if __name__ == "__main__":
    if "--now" in sys.argv:
        run_daily_job()
    else:
        try:
            import schedule
            import time

            schedule.every().day.at("08:30").do(run_daily_job)
            logger.info("Scheduler started. Will run daily at 08:30.")
            while True:
                schedule.run_pending()
                time.sleep(60)
        except ImportError:
            logger.error("'schedule' package not installed. Run: pip install schedule")
            sys.exit(1)
