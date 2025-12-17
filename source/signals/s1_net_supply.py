"""S1: Net Supply Change signal calculator."""

from typing import Any

from source.config import settings
from source.signals.base import BaseSignal, SignalResult, SignalValue


class NetSupplySignal(BaseSignal):
    """
    S1: Net Supply Change

    Measures the net change in ETH supply (emission - burn).
    Deflation (burn > emission) is bullish, inflation is bearish.

    Input:
    - emission_eth: Daily ETH emission from staking rewards
    - burn_eth: Daily ETH burned via EIP-1559

    Output:
    - +1: Deflationary (net burn > threshold)
    - 0: Neutral
    - -1: Inflationary (net emission > threshold)
    """

    def __init__(self):
        super().__init__(
            name="S1_NetSupply",
            description="Net Supply Change (Emission - Burn)",
        )
        self.bullish_threshold = settings.thresholds.s1_bullish  # -1000 ETH/day
        self.bearish_threshold = settings.thresholds.s1_bearish  # +1000 ETH/day

    def calculate(self, data: dict[str, Any]) -> SignalResult:
        """
        Calculate net supply signal.

        Args:
            data: Dict with keys:
                - emission_7d_eth: ETH emitted in last 7 days
                - burn_7d_eth: ETH burned in last 7 days
                OR
                - net_supply_change_daily: Pre-calculated daily net change
        """
        # Calculate daily net supply change
        if "net_supply_change_daily" in data:
            net_daily = data["net_supply_change_daily"]
        else:
            emission_7d = data.get("emission_7d_eth", 0)
            burn_7d = data.get("burn_7d_eth", 0)
            net_weekly = emission_7d - burn_7d
            net_daily = net_weekly / 7

        # Convert to signal
        # Negative net = deflationary = bullish
        # Note: thresholds are set up so bullish_threshold is negative
        signal = self._to_signal(
            value=net_daily,
            bullish_threshold=self.bullish_threshold,  # -1000
            bearish_threshold=self.bearish_threshold,   # +1000
            invert=True,  # Lower (more negative) is better
        )

        result = SignalResult(
            name=self.name,
            value=signal,
            raw_value=net_daily,
            interpretation=self._get_interpretation(signal),
            details={
                "net_supply_daily_eth": net_daily,
                "bullish_threshold": self.bullish_threshold,
                "bearish_threshold": self.bearish_threshold,
                "is_deflationary": net_daily < 0,
            },
        )

        self.log_calculation(result)
        return result
