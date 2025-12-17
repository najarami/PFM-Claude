"""Tests for EFI calculator and interpreter."""

import pytest
from datetime import datetime

from source.engine.efi_calculator import EFICalculator, EFIResult
from source.engine.interpreter import EFIInterpreter


class TestEFICalculator:
    """Tests for EFI calculator."""

    @pytest.fixture
    def calculator(self):
        return EFICalculator()

    @pytest.mark.asyncio
    async def test_calculate_with_manual_data_all_bullish(self, calculator):
        """Test EFI calculation with all bullish signals."""
        result = await calculator.calculate_with_manual_data(
            s1_data={"net_supply_change_daily": -2000},  # Deflationary
            s2_data={"net_staking_flow_eth": 20_000},    # Net staking
            s3_data={"weekly_flow_usd": 100_000_000},    # ETF inflows
            s4_data={"net_flow_7d_eth": -100_000},       # Exchange outflows
            s5_data={
                "oi_change_7d_pct": 0.05,
                "funding_rate": 0.005,
                "liquidations_7d_usd": 50_000_000,
            },  # Healthy market
        )

        assert result.efi_value == 5  # All signals bullish
        assert len(result.signals) == 5

    @pytest.mark.asyncio
    async def test_calculate_with_manual_data_all_bearish(self, calculator):
        """Test EFI calculation with all bearish signals."""
        result = await calculator.calculate_with_manual_data(
            s1_data={"net_supply_change_daily": 2000},   # Inflationary
            s2_data={"net_staking_flow_eth": -20_000},   # Net unstaking
            s3_data={"weekly_flow_usd": -100_000_000},   # ETF outflows
            s4_data={"net_flow_7d_eth": 100_000},        # Exchange inflows
            s5_data={
                "oi_change_7d_pct": 0.30,
                "funding_rate": 0.08,
                "liquidations_7d_usd": 600_000_000,
            },  # Stressed market
        )

        assert result.efi_value == -5  # All signals bearish

    @pytest.mark.asyncio
    async def test_calculate_with_manual_data_mixed(self, calculator):
        """Test EFI calculation with mixed signals."""
        result = await calculator.calculate_with_manual_data(
            s1_data={"net_supply_change_daily": -2000},  # Bullish (+1)
            s2_data={"net_staking_flow_eth": 0},         # Neutral (0)
            s3_data={"weekly_flow_usd": -100_000_000},   # Bearish (-1)
            s4_data={"net_flow_7d_eth": -100_000},       # Bullish (+1)
            s5_data={
                "oi_change_7d_pct": 0.15,
                "funding_rate": 0.03,
                "liquidations_7d_usd": 150_000_000,
            },  # Neutral (0)
        )

        assert result.efi_value == 1  # +1 + 0 - 1 + 1 + 0 = 1

    @pytest.mark.asyncio
    async def test_result_has_timestamp(self, calculator):
        """Test that result includes timestamp."""
        result = await calculator.calculate_with_manual_data()
        assert isinstance(result.timestamp, datetime)

    @pytest.mark.asyncio
    async def test_result_has_all_signals(self, calculator):
        """Test that result includes all 5 signals."""
        result = await calculator.calculate_with_manual_data()
        assert "S1" in result.signals
        assert "S2" in result.signals
        assert "S3" in result.signals
        assert "S4" in result.signals
        assert "S5" in result.signals


class TestEFIInterpreter:
    """Tests for EFI interpreter."""

    @pytest.fixture
    def interpreter(self):
        return EFIInterpreter()

    @pytest.fixture
    def mock_result(self):
        """Create a mock EFI result for testing."""
        from source.signals.base import SignalResult

        return EFIResult(
            timestamp=datetime.now(),
            efi_value=3,
            signals={
                "S1": SignalResult(
                    name="S1", value=1, raw_value=-1500, interpretation="Bullish"
                ),
                "S2": SignalResult(
                    name="S2", value=1, raw_value=15000, interpretation="Bullish"
                ),
                "S3": SignalResult(
                    name="S3", value=0, raw_value=30000000, interpretation="Neutral"
                ),
                "S4": SignalResult(
                    name="S4", value=1, raw_value=-60000, interpretation="Bullish"
                ),
                "S5": SignalResult(
                    name="S5", value=0, raw_value=0.35, interpretation="Low Stress"
                ),
            },
            raw_data={},
        )

    def test_classify_explosive(self, interpreter):
        """Test Explosive regime classification."""
        assert interpreter._classify_regime(5) == "Explosive"
        assert interpreter._classify_regime(4) == "Explosive"

    def test_classify_constructive(self, interpreter):
        """Test Constructive regime classification."""
        assert interpreter._classify_regime(3) == "Constructive"
        assert interpreter._classify_regime(2) == "Constructive"

    def test_classify_neutral(self, interpreter):
        """Test Neutral regime classification."""
        assert interpreter._classify_regime(1) == "Neutral"
        assert interpreter._classify_regime(0) == "Neutral"
        assert interpreter._classify_regime(-1) == "Neutral"

    def test_classify_fragile(self, interpreter):
        """Test Fragile regime classification."""
        assert interpreter._classify_regime(-2) == "Fragile"
        assert interpreter._classify_regime(-3) == "Fragile"

    def test_classify_stress(self, interpreter):
        """Test Stress regime classification."""
        assert interpreter._classify_regime(-4) == "Stress"
        assert interpreter._classify_regime(-5) == "Stress"

    def test_interpret_result(self, interpreter, mock_result):
        """Test full interpretation of result."""
        interpretation = interpreter.interpret(mock_result)

        assert interpretation.regime == "Constructive"
        assert interpretation.risk_level == "Low"
        assert len(interpretation.signal_breakdown) == 5

    def test_regime_colors(self, interpreter):
        """Test regime color mapping."""
        assert interpreter.get_regime_color("Explosive") == "bright_green"
        assert interpreter.get_regime_color("Stress") == "red"

    def test_compare_with_previous(self, interpreter, mock_result):
        """Test comparison between current and previous results."""
        from source.signals.base import SignalResult

        previous = EFIResult(
            timestamp=datetime.now(),
            efi_value=1,
            signals={
                "S1": SignalResult(
                    name="S1", value=0, raw_value=0, interpretation="Neutral"
                ),
                "S2": SignalResult(
                    name="S2", value=1, raw_value=15000, interpretation="Bullish"
                ),
                "S3": SignalResult(
                    name="S3", value=0, raw_value=30000000, interpretation="Neutral"
                ),
                "S4": SignalResult(
                    name="S4", value=0, raw_value=0, interpretation="Neutral"
                ),
                "S5": SignalResult(
                    name="S5", value=0, raw_value=0.35, interpretation="Low Stress"
                ),
            },
            raw_data={},
        )

        comparison = interpreter.compare_with_previous(mock_result, previous)

        assert comparison["efi_change"] == "+2"
        assert comparison["trend"] == "Strongly Improving"
        assert comparison["signal_changes"]["S1"] == "improved"
        assert comparison["signal_changes"]["S2"] == "unchanged"
