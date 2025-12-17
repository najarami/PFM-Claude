"""EFI Interpreter - regime classification and recommendations."""

from typing import Literal
from pydantic import BaseModel

from source.engine.efi_calculator import EFIResult


Regime = Literal["Explosive", "Constructive", "Neutral", "Fragile", "Stress"]


class EFIInterpretation(BaseModel):
    """Interpretation of an EFI result."""

    regime: Regime
    description: str
    recommendation: str
    risk_level: Literal["Low", "Medium", "High"]
    signal_breakdown: dict[str, str]


class EFIInterpreter:
    """
    Interprets EFI values and classifies market regimes.

    Regime Classification:
    - Explosive (+4 to +5): Strong bullish alignment
    - Constructive (+1 to +3): Moderately bullish
    - Neutral (-1 to +1): Mixed signals
    - Fragile (-2 to -3): Moderately bearish
    - Stress (-4 to -5): Strong bearish alignment
    """

    REGIME_DESCRIPTIONS = {
        "Explosive": "All or most signals aligned bullish. Strong supply absorption.",
        "Constructive": "Mostly bullish signals. Favorable accumulation dynamics.",
        "Neutral": "Mixed signals. No clear directional bias.",
        "Fragile": "Mostly bearish signals. Distribution phase likely.",
        "Stress": "All or most signals aligned bearish. Risk-off environment.",
    }

    REGIME_RECOMMENDATIONS = {
        "Explosive": "Consider full position. High conviction environment.",
        "Constructive": "Maintain or build position. DCA favorable.",
        "Neutral": "Reduce position size. Wait for clarity.",
        "Fragile": "Defensive positioning. Consider reducing exposure.",
        "Stress": "Maximum caution. Preserve capital.",
    }

    REGIME_RISK = {
        "Explosive": "Low",
        "Constructive": "Low",
        "Neutral": "Medium",
        "Fragile": "Medium",
        "Stress": "High",
    }

    def interpret(self, result: EFIResult) -> EFIInterpretation:
        """
        Interpret an EFI result and classify the market regime.

        Args:
            result: EFIResult from calculator

        Returns:
            EFIInterpretation with regime, description, and recommendation
        """
        regime = self._classify_regime(result.efi_value)

        # Generate signal breakdown
        signal_breakdown = {}
        for name, signal in result.signals.items():
            signal_breakdown[name] = (
                f"{signal.interpretation} ({signal.value:+d}): "
                f"raw={signal.raw_value:.2f}"
            )

        return EFIInterpretation(
            regime=regime,
            description=self.REGIME_DESCRIPTIONS[regime],
            recommendation=self.REGIME_RECOMMENDATIONS[regime],
            risk_level=self.REGIME_RISK[regime],
            signal_breakdown=signal_breakdown,
        )

    def _classify_regime(self, efi_value: int) -> Regime:
        """Classify EFI value into a regime."""
        if efi_value >= 4:
            return "Explosive"
        elif efi_value >= 2:
            return "Constructive"
        elif efi_value >= -1:
            return "Neutral"
        elif efi_value >= -3:
            return "Fragile"
        else:
            return "Stress"

    def get_regime_color(self, regime: Regime) -> str:
        """Get color code for regime (for CLI display)."""
        colors = {
            "Explosive": "bright_green",
            "Constructive": "green",
            "Neutral": "yellow",
            "Fragile": "orange1",
            "Stress": "red",
        }
        return colors.get(regime, "white")

    def get_efi_emoji(self, efi_value: int) -> str:
        """Get emoji representation of EFI value."""
        if efi_value >= 4:
            return "🚀"
        elif efi_value >= 2:
            return "📈"
        elif efi_value >= -1:
            return "➡️"
        elif efi_value >= -3:
            return "📉"
        else:
            return "🔻"

    def compare_with_previous(
        self,
        current: EFIResult,
        previous: EFIResult,
    ) -> dict[str, str]:
        """
        Compare current EFI with previous week.

        Returns dict with change analysis.
        """
        efi_change = current.efi_value - previous.efi_value

        # Analyze signal changes
        signal_changes = {}
        for name in current.signals:
            if name in previous.signals:
                curr_val = current.signals[name].value
                prev_val = previous.signals[name].value
                change = curr_val - prev_val
                if change > 0:
                    signal_changes[name] = "improved"
                elif change < 0:
                    signal_changes[name] = "deteriorated"
                else:
                    signal_changes[name] = "unchanged"

        # Determine trend
        if efi_change >= 2:
            trend = "Strongly Improving"
        elif efi_change >= 1:
            trend = "Improving"
        elif efi_change == 0:
            trend = "Stable"
        elif efi_change >= -1:
            trend = "Weakening"
        else:
            trend = "Strongly Weakening"

        return {
            "efi_change": f"{efi_change:+d}",
            "trend": trend,
            "signal_changes": signal_changes,
            "previous_regime": self._classify_regime(previous.efi_value),
            "current_regime": self._classify_regime(current.efi_value),
        }
