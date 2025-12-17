"""Tests for signal calculators."""

import pytest
from source.signals import (
    NetSupplySignal,
    StakingSignal,
    ETFDemandSignal,
    ExchangeFlowSignal,
    LeverageSignal,
)


class TestNetSupplySignal:
    """Tests for S1: Net Supply Change signal."""

    def setup_method(self):
        self.signal = NetSupplySignal()

    def test_bullish_deflationary(self):
        """Test bullish signal when supply is deflationary."""
        data = {"net_supply_change_daily": -2000}  # Strong deflation
        result = self.signal.calculate(data)
        assert result.value == 1
        assert result.interpretation == "Bullish"

    def test_bearish_inflationary(self):
        """Test bearish signal when supply is inflationary."""
        data = {"net_supply_change_daily": 2000}  # Strong inflation
        result = self.signal.calculate(data)
        assert result.value == -1
        assert result.interpretation == "Bearish"

    def test_neutral(self):
        """Test neutral signal when supply change is minimal."""
        data = {"net_supply_change_daily": 0}
        result = self.signal.calculate(data)
        assert result.value == 0
        assert result.interpretation == "Neutral"

    def test_from_weekly_data(self):
        """Test calculation from weekly emission and burn data."""
        data = {
            "emission_7d_eth": 11_900,
            "burn_7d_eth": 14_000,
        }
        result = self.signal.calculate(data)
        # Net daily = (11900 - 14000) / 7 = -300 ETH/day (deflationary)
        assert result.value == 0  # Within neutral threshold
        assert result.raw_value == pytest.approx(-300, rel=0.01)


class TestStakingSignal:
    """Tests for S2: Staking Net Flow signal."""

    def setup_method(self):
        self.signal = StakingSignal()

    def test_bullish_net_staking(self):
        """Test bullish signal when net staking is positive."""
        data = {"net_staking_flow_eth": 20_000}
        result = self.signal.calculate(data)
        assert result.value == 1
        assert result.interpretation == "Bullish"

    def test_bearish_net_unstaking(self):
        """Test bearish signal when net unstaking occurs."""
        data = {"net_staking_flow_eth": -20_000}
        result = self.signal.calculate(data)
        assert result.value == -1
        assert result.interpretation == "Bearish"

    def test_neutral(self):
        """Test neutral signal when staking flow is balanced."""
        data = {"net_staking_flow_eth": 5_000}
        result = self.signal.calculate(data)
        assert result.value == 0
        assert result.interpretation == "Neutral"

    def test_from_deposits_withdrawals(self):
        """Test calculation from deposits and withdrawals."""
        data = {
            "deposits_7d_eth": 60_000,
            "withdrawals_7d_eth": 40_000,
        }
        result = self.signal.calculate(data)
        # Net flow = 60000 - 40000 = 20000
        assert result.value == 1  # Bullish


class TestETFDemandSignal:
    """Tests for S3: ETF/Institutional Demand signal."""

    def setup_method(self):
        self.signal = ETFDemandSignal()

    def test_bullish_inflows(self):
        """Test bullish signal when significant inflows."""
        data = {"weekly_flow_usd": 100_000_000}  # $100M inflows
        result = self.signal.calculate(data)
        assert result.value == 1
        assert result.interpretation == "Bullish"

    def test_bearish_outflows(self):
        """Test bearish signal when significant outflows."""
        data = {"weekly_flow_usd": -100_000_000}  # $100M outflows
        result = self.signal.calculate(data)
        assert result.value == -1
        assert result.interpretation == "Bearish"

    def test_neutral_markets_closed(self):
        """Test neutral signal when markets are closed."""
        data = {"weekly_flow_usd": 100_000_000, "markets_open": False}
        result = self.signal.calculate(data)
        assert result.value == 0
        assert result.interpretation == "Markets Closed"


class TestExchangeFlowSignal:
    """Tests for S4: Exchange Net Flow signal."""

    def setup_method(self):
        self.signal = ExchangeFlowSignal()

    def test_bullish_outflows(self):
        """Test bullish signal when exchange outflows dominate."""
        data = {"net_flow_7d_eth": -100_000}  # Net outflows
        result = self.signal.calculate(data)
        assert result.value == 1
        assert result.interpretation == "Bullish"

    def test_bearish_inflows(self):
        """Test bearish signal when exchange inflows dominate."""
        data = {"net_flow_7d_eth": 100_000}  # Net inflows
        result = self.signal.calculate(data)
        assert result.value == -1
        assert result.interpretation == "Bearish"

    def test_neutral(self):
        """Test neutral signal when flows are balanced."""
        data = {"net_flow_7d_eth": 0}
        result = self.signal.calculate(data)
        assert result.value == 0
        assert result.interpretation == "Neutral"


class TestLeverageSignal:
    """Tests for S5: Leverage & Stress signal."""

    def setup_method(self):
        self.signal = LeverageSignal()

    def test_healthy_market(self):
        """Test bullish signal when market is healthy."""
        data = {
            "oi_change_7d_pct": 0.05,
            "funding_rate": 0.005,
            "liquidations_7d_usd": 50_000_000,
        }
        result = self.signal.calculate(data)
        assert result.value == 1
        assert "Healthy" in result.interpretation

    def test_stressed_market(self):
        """Test bearish signal when market is stressed."""
        data = {
            "oi_change_7d_pct": 0.30,  # High OI change
            "funding_rate": 0.08,      # High funding
            "liquidations_7d_usd": 600_000_000,  # High liquidations
        }
        result = self.signal.calculate(data)
        assert result.value == -1
        assert "Stress" in result.interpretation

    def test_moderate_stress(self):
        """Test neutral signal when stress is moderate."""
        data = {
            "oi_change_7d_pct": 0.15,
            "funding_rate": 0.03,
            "liquidations_7d_usd": 150_000_000,
        }
        result = self.signal.calculate(data)
        assert result.value == 0  # Neutral


class TestSignalDetails:
    """Test signal details and metadata."""

    def test_signal_has_name(self):
        """Test that signals have proper names."""
        signal = NetSupplySignal()
        result = signal.calculate({"net_supply_change_daily": 0})
        assert result.name == "S1_NetSupply"

    def test_signal_has_details(self):
        """Test that signals include calculation details."""
        signal = StakingSignal()
        data = {"net_staking_flow_eth": 15_000}
        result = signal.calculate(data)
        assert "net_staking_flow_eth" in result.details
        assert "bullish_threshold" in result.details
