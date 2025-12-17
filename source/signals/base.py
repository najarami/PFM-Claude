"""Base signal class for EFI signal calculations."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Literal
from pydantic import BaseModel

logger = logging.getLogger(__name__)


SignalValue = Literal[-1, 0, 1]


class SignalResult(BaseModel):
    """Result of a signal calculation."""

    name: str
    value: SignalValue
    raw_value: float
    interpretation: str
    details: dict[str, Any] = {}


class BaseSignal(ABC):
    """Base class for all signal calculators."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def calculate(self, data: dict[str, Any]) -> SignalResult:
        """
        Calculate the signal value from input data.

        Returns:
            SignalResult with value -1 (bearish), 0 (neutral), or +1 (bullish)
        """

    def _to_signal(
        self,
        value: float,
        bullish_threshold: float,
        bearish_threshold: float,
        invert: bool = False,
    ) -> SignalValue:
        """
        Convert a raw value to a signal (-1, 0, +1).

        Args:
            value: The raw metric value
            bullish_threshold: Value above which signal is +1
            bearish_threshold: Value below which signal is -1
            invert: If True, invert the comparison logic

        Returns:
            -1 (bearish), 0 (neutral), or +1 (bullish)
        """
        if invert:
            # For metrics where lower = bullish (e.g., exchange inflows)
            if value <= bullish_threshold:
                return 1
            elif value >= bearish_threshold:
                return -1
            return 0
        else:
            # Standard: higher = bullish
            if value >= bullish_threshold:
                return 1
            elif value <= bearish_threshold:
                return -1
            return 0

    def _get_interpretation(self, signal: SignalValue) -> str:
        """Get human-readable interpretation of signal."""
        if signal == 1:
            return "Bullish"
        elif signal == -1:
            return "Bearish"
        return "Neutral"

    def log_calculation(self, result: SignalResult) -> None:
        """Log signal calculation for debugging."""
        logger.info(
            f"{self.name}: raw={result.raw_value:.2f} -> signal={result.value} "
            f"({result.interpretation})"
        )
