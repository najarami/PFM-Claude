"""S5: Leverage & Stress signal calculator."""

from typing import Any

from source.config import settings
from source.signals.base import BaseSignal, SignalResult, SignalValue


class LeverageSignal(BaseSignal):
    """
    S5: Leverage & Stress

    Measures market stress via derivatives metrics.
    Low leverage/stress = healthy market = bullish.
    High leverage/stress = fragile market = bearish.

    Input:
    - oi_change_7d_pct: Open Interest change percentage
    - funding_rate: Average funding rate
    - liquidations_7d_usd: Total liquidations in 7 days

    Output:
    - +1: Healthy market (low stress)
    - 0: Neutral
    - -1: Stressed market (high leverage risk)
    """

    def __init__(self):
        super().__init__(
            name="S5_Leverage",
            description="Leverage & Market Stress",
        )
        self.stress_oi_threshold = settings.thresholds.s5_stress_oi_change  # 20%
        self.stress_funding_threshold = settings.thresholds.s5_stress_funding  # 5%

    def calculate(self, data: dict[str, Any]) -> SignalResult:
        """
        Calculate leverage/stress signal.

        Args:
            data: Dict with keys:
                - oi_change_7d_pct: OI change as decimal (0.05 = 5%)
                - funding_rate: Funding rate as decimal (0.01 = 1%)
                - liquidations_7d_usd: Total liquidations in USD
        """
        oi_change = abs(data.get("oi_change_7d_pct", 0))
        funding = abs(data.get("funding_rate", 0))
        liquidations = data.get("liquidations_7d_usd", 0)

        # Calculate stress score (0-1)
        stress_score = self._calculate_stress_score(oi_change, funding, liquidations)

        # Convert to signal
        # Lower stress = bullish
        if stress_score < 0.3:
            signal: SignalValue = 1  # Healthy
        elif stress_score > 0.6:
            signal = -1  # Stressed
        else:
            signal = 0  # Neutral

        interpretation = self._get_stress_interpretation(stress_score)

        result = SignalResult(
            name=self.name,
            value=signal,
            raw_value=stress_score,
            interpretation=interpretation,
            details={
                "stress_score": stress_score,
                "oi_change_7d_pct": oi_change,
                "funding_rate": funding,
                "liquidations_7d_usd": liquidations,
                "stress_factors": self._get_stress_factors(oi_change, funding, liquidations),
                "is_estimated": data.get("is_estimated", False),
            },
        )

        self.log_calculation(result)
        return result

    def _calculate_stress_score(
        self,
        oi_change: float,
        funding: float,
        liquidations: float,
    ) -> float:
        """
        Calculate composite stress score from 0 (healthy) to 1 (extreme stress).
        """
        stress = 0.0

        # OI change component (weight: 30%)
        if oi_change > self.stress_oi_threshold:
            stress += 0.30 * min(oi_change / self.stress_oi_threshold, 2.0) / 2.0
        else:
            stress += 0.30 * (oi_change / self.stress_oi_threshold)

        # Funding rate component (weight: 30%)
        if funding > self.stress_funding_threshold:
            stress += 0.30 * min(funding / self.stress_funding_threshold, 2.0) / 2.0
        else:
            stress += 0.30 * (funding / self.stress_funding_threshold)

        # Liquidations component (weight: 40%)
        # Thresholds: $100M low, $300M medium, $500M high
        if liquidations > 500_000_000:
            stress += 0.40
        elif liquidations > 300_000_000:
            stress += 0.30
        elif liquidations > 100_000_000:
            stress += 0.15

        return min(stress, 1.0)

    def _get_stress_factors(
        self,
        oi_change: float,
        funding: float,
        liquidations: float,
    ) -> list[str]:
        """Identify which factors are contributing to stress."""
        factors = []

        if oi_change > self.stress_oi_threshold:
            factors.append(f"High OI change ({oi_change:.1%})")

        if funding > self.stress_funding_threshold:
            factors.append(f"High funding rate ({funding:.2%})")

        if liquidations > 200_000_000:
            factors.append(f"Significant liquidations (${liquidations/1e6:.0f}M)")

        return factors if factors else ["No significant stress factors"]

    def _get_stress_interpretation(self, stress_score: float) -> str:
        """Get human-readable stress interpretation."""
        if stress_score < 0.2:
            return "Healthy"
        elif stress_score < 0.4:
            return "Low Stress"
        elif stress_score < 0.6:
            return "Moderate Stress"
        elif stress_score < 0.8:
            return "High Stress"
        else:
            return "Extreme Stress"
