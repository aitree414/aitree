from abc import ABC, abstractmethod
from datetime import datetime, timedelta


class BaseScreener(ABC):
    """Abstract base class for all screener strategies."""

    def __init__(self, thresholds: dict):
        self.thresholds = thresholds

    @abstractmethod
    def screen(self, symbols: list[str]) -> list[dict]:
        """
        Screen a list of symbols and return matching results.

        Each result dict: {symbol, name, score, signals, reason}
        - score: 0.0–1.0 (higher = stronger signal)
        - signals: list of triggered signal names
        - reason: human-readable summary
        """

    def _lookback_dates(self, days: int = 60) -> tuple[str, str]:
        end = datetime.today()
        start = end - timedelta(days=days)
        return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
