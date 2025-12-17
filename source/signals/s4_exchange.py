"""S4: Exchange Net Flow signal calculator."""

from typing import Any

from source.config import settings
from source.signals.base import BaseSignal, SignalResult, SignalValue


class ExchangeFlowSignal(BaseSignal):
    """
    S4: Exchange Net Flow

    Measures net ETH flowing into/out of exchanges.
    Outflows (withdrawals > deposits) = bullish (accumulation).
    Inflows (deposits > withdrawals) = bearish (distribution).

    Input:
    - inflows_7d_eth: ETH deposited to exchanges
    - outflows_7d_eth: ETH withdrawn from exchanges

    Output:
    - +1: Net outflows (bullish - accumulation)
    - 0: Neutral
    - -1: Net inflows (bearish - distribution)
    """

    def __init__(self):
        super().__init__(
            name="S4_Exchange",
            description="Exchange Net Flow",
        )
        # Note: thresholds are for net flow (inflows - outflows)
        # Negative net = outflows > inflows = bullish
        self.bullish_threshold = settings.thresholds.s4_bullish  # -50000 ETH
        self.bearish_threshold = settings.thresholds.s4_bearish  # +50000 ETH

    def calculate(self, data: dict[str, Any]) -> SignalResult:
        """
        Calculate exchange flow signal.

        Args:
            data: Dict with keys:
                - inflows_7d_eth: ETH deposited to exchanges
                - outflows_7d_eth: ETH withdrawn from exchanges
                OR
                - net_flow_7d_eth: Pre-calculated net flow
        """
        # Calculate net flow (inflows - outflows)
        if "net_flow_7d_eth" in data:
            net_flow = data["net_flow_7d_eth"]
        else:
            inflows = data.get("inflows_7d_eth", 0)
            outflows = data.get("outflows_7d_eth", 0)
            net_flow = inflows - outflows

        # Convert to signal
        # Negative net flow (more outflows) = bullish
        signal = self._to_signal(
            value=net_flow,
            bullish_threshold=self.bullish_threshold,  # -50000
            bearish_threshold=self.bearish_threshold,   # +50000
            invert=True,  # Lower (more negative) is better
        )

        result = SignalResult(
            name=self.name,
            value=signal,
            raw_value=net_flow,
            interpretation=self._get_interpretation(signal),
            details={
                "net_flow_7d_eth": net_flow,
                "inflows_7d_eth": data.get("inflows_7d_eth"),
                "outflows_7d_eth": data.get("outflows_7d_eth"),
                "bullish_threshold": self.bullish_threshold,
                "bearish_threshold": self.bearish_threshold,
                "is_accumulation": net_flow < 0,
                "is_estimated": data.get("is_estimated", False),
            },
        )

        self.log_calculation(result)
        return result
