"""S2: Staking Net Flow signal calculator."""

from typing import Any

from source.config import settings
from source.signals.base import BaseSignal, SignalResult, SignalValue


class StakingSignal(BaseSignal):
    """
    S2: Staking Net Flow

    Measures net ETH flowing into/out of staking.
    Net staking (deposits > withdrawals) reduces liquid supply = bullish.

    Input:
    - deposits_7d_eth: ETH deposited to validators in 7 days
    - withdrawals_7d_eth: ETH withdrawn from validators in 7 days

    Output:
    - +1: Net staking (bullish - supply absorbed)
    - 0: Neutral
    - -1: Net unstaking (bearish - supply released)
    """

    def __init__(self):
        super().__init__(
            name="S2_Staking",
            description="Staking Net Flow (Deposits - Withdrawals)",
        )
        self.bullish_threshold = settings.thresholds.s2_bullish  # +10000 ETH/week
        self.bearish_threshold = settings.thresholds.s2_bearish  # -10000 ETH/week

    def calculate(self, data: dict[str, Any]) -> SignalResult:
        """
        Calculate staking flow signal.

        Args:
            data: Dict with keys:
                - deposits_7d_eth: ETH deposited in last 7 days
                - withdrawals_7d_eth: ETH withdrawn in last 7 days
                OR
                - net_staking_flow_eth: Pre-calculated net flow
        """
        # Calculate net staking flow
        if "net_staking_flow_eth" in data:
            net_flow = data["net_staking_flow_eth"]
        else:
            deposits = data.get("deposits_7d_eth", 0)
            withdrawals = data.get("withdrawals_7d_eth", 0)
            net_flow = deposits - withdrawals

        # Convert to signal
        # Positive net flow (more deposits) = bullish
        signal = self._to_signal(
            value=net_flow,
            bullish_threshold=self.bullish_threshold,  # +10000
            bearish_threshold=self.bearish_threshold,  # -10000
            invert=False,
        )

        result = SignalResult(
            name=self.name,
            value=signal,
            raw_value=net_flow,
            interpretation=self._get_interpretation(signal),
            details={
                "net_staking_flow_eth": net_flow,
                "deposits_7d_eth": data.get("deposits_7d_eth"),
                "withdrawals_7d_eth": data.get("withdrawals_7d_eth"),
                "bullish_threshold": self.bullish_threshold,
                "bearish_threshold": self.bearish_threshold,
            },
        )

        self.log_calculation(result)
        return result
