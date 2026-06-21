from abc import ABC, abstractmethod

class StrategyBase(ABC):
    """Base class for strategies"""

    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def analyze_and_trade(self, bot, index: str) -> None:
        """Perform analysis for `index` and place trades via the provided `bot` instance."""
        pass
