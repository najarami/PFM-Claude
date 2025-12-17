"""S3: ETF/Institutional Demand signal calculator."""

from typing import Any

from source.config import settings
from source.signals.base import BaseSignal, SignalResult, SignalValue


class ETFDemandSignal(BaseSignal):
    """
    S3: ETF/Institutional Demand

    Measures institutional demand via ETH ETF flows.
    Inflows indicate institutional buying = bullish.

    Input:
    - weekly_flow_usd: Net ETF flow in USD for the week

    Output:
    - +1: Significant inflows (bullish)
    - 0: Neutral
    - -1: Significant outflows (bearish)
    """

    def __init__(self):
        super().__init__(
            name="S3_ETF",
            description="ETF/Institutional Demand",
        )
        self.bullish_threshold = settings.thresholds.s3_bullish  # +$50M/week
        self.bearish_threshold = settings.thresholds.s3_bearish  # -$50M/week

    def calculate(self, data: dict[str, Any]) -> SignalResult:
        """
        Calculate ETF demand signal.

        Args:
            data: Dict with keys:
                - weekly_flow_usd: Net ETF flow in USD for the week
                - markets_open: Whether markets were open (optional)
        """
        weekly_flow = data.get("weekly_flow_usd", 0)
        markets_open = data.get("markets_open", True)

        # If markets were closed, return neutral
        if not markets_open:
            signal: SignalValue = 0
            interpretation = "Markets Closed"
        else:
            # Convert to signal
            # Positive flow (inflows) = bullish
            signal = self._to_signal(
                value=weekly_flow,
                bullish_threshold=self.bullish_threshold,
                bearish_threshold=self.bearish_threshold,
                invert=False,
            )
            interpretation = self._get_interpretation(signal)

        result = SignalResult(
            name=self.name,
            value=signal,
            raw_value=weekly_flow,
            interpretation=interpretation,
            details={
                "weekly_flow_usd": weekly_flow,
                "weekly_flow_usd_millions": weekly_flow / 1_000_000,
                "markets_open": markets_open,
                "bullish_threshold_millions": self.bullish_threshold / 1_000_000,
                "bearish_threshold_millions": self.bearish_threshold / 1_000_000,
                "is_estimated": data.get("is_estimated", False),
            },
        )

        self.log_calculation(result)
        return result
