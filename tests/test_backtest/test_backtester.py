"""Tests for backtest module."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from source.backtest.signal_simulator import SignalSimulator, TradingAction
from source.backtest.backtester import Backtester, BacktestResult, Trade
from source.backtest.metrics import BacktestMetrics, PerformanceMetrics


class TestSignalSimulator:
    """Tests for SignalSimulator class."""

    @pytest.fixture
    def simulator(self):
        return SignalSimulator()

    @pytest.fixture
    def sample_price_data(self):
        """Create sample price data for testing."""
        dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
        # Create a price series with some trend and volatility
        np.random.seed(42)
        base_price = 1500
        returns = np.random.normal(0.001, 0.03, 100)
        prices = base_price * np.cumprod(1 + returns)

        return pd.DataFrame({
            "date": dates,
            "price": prices,
            "volume": np.random.uniform(1e9, 5e9, 100),
        })

    def test_simulate_signals_returns_dataframe(self, simulator, sample_price_data):
        """Test that simulate_signals returns a DataFrame with expected columns."""
        result = simulator.simulate_signals(sample_price_data)

        assert isinstance(result, pd.DataFrame)
        assert "efi_value" in result.columns
        assert "regime" in result.columns
        assert "action" in result.columns
        assert "s1_value" in result.columns
        assert "s2_value" in result.columns
        assert "s3_value" in result.columns
        assert "s4_value" in result.columns
        assert "s5_value" in result.columns

    def test_efi_value_bounded(self, simulator, sample_price_data):
        """Test that EFI values are bounded between -5 and +5."""
        result = simulator.simulate_signals(sample_price_data)

        assert result["efi_value"].min() >= -5
        assert result["efi_value"].max() <= 5

    def test_signal_components_bounded(self, simulator, sample_price_data):
        """Test that individual signal components are bounded between -1 and +1."""
        result = simulator.simulate_signals(sample_price_data)

        for col in ["s1_value", "s2_value", "s3_value", "s4_value", "s5_value"]:
            assert result[col].min() >= -1
            assert result[col].max() <= 1

    def test_action_values_valid(self, simulator, sample_price_data):
        """Test that action values are valid."""
        result = simulator.simulate_signals(sample_price_data)

        valid_actions = {"BUY", "HOLD", "SELL"}
        assert set(result["action"].unique()).issubset(valid_actions)

    def test_regime_classification(self, simulator):
        """Test regime classification logic."""
        assert simulator._classify_regime(5) == "Explosive"
        assert simulator._classify_regime(4) == "Explosive"
        assert simulator._classify_regime(3) == "Constructive"
        assert simulator._classify_regime(2) == "Constructive"
        assert simulator._classify_regime(1) == "Neutral"
        assert simulator._classify_regime(0) == "Neutral"
        assert simulator._classify_regime(-1) == "Neutral"
        assert simulator._classify_regime(-2) == "Fragile"
        assert simulator._classify_regime(-3) == "Fragile"
        assert simulator._classify_regime(-4) == "Stress"
        assert simulator._classify_regime(-5) == "Stress"

    def test_action_thresholds(self, simulator):
        """Test action threshold logic."""
        assert simulator._get_action(5) == "BUY"
        assert simulator._get_action(2) == "BUY"
        assert simulator._get_action(1) == "HOLD"
        assert simulator._get_action(0) == "HOLD"
        assert simulator._get_action(-1) == "HOLD"
        assert simulator._get_action(-2) == "SELL"
        assert simulator._get_action(-5) == "SELL"


class TestBacktester:
    """Tests for Backtester class."""

    @pytest.fixture
    def backtester(self):
        return Backtester(initial_investment=100.0)

    @pytest.fixture
    def sample_signals_data(self):
        """Create sample signals data for testing."""
        dates = pd.date_range(start="2023-01-01", periods=50, freq="D")
        # Simple price that doubles
        prices = np.linspace(1000, 2000, 50)

        # Alternating signals for testing
        actions = ["HOLD"] * 50
        actions[5] = "BUY"   # Buy early
        actions[25] = "SELL"  # Sell in middle
        actions[30] = "BUY"   # Buy again
        actions[45] = "SELL"  # Sell near end

        return pd.DataFrame({
            "date": dates,
            "price": prices,
            "efi_value": [0] * 50,
            "action": actions,
        })

    def test_run_backtest_returns_result(self, backtester, sample_signals_data):
        """Test that run_backtest returns a BacktestResult."""
        result = backtester.run_backtest(sample_signals_data)

        assert isinstance(result, BacktestResult)
        assert result.initial_investment == 100.0
        assert result.final_value > 0
        assert isinstance(result.trades, list)

    def test_backtest_executes_trades(self, backtester, sample_signals_data):
        """Test that backtest executes expected number of trades."""
        result = backtester.run_backtest(sample_signals_data)

        # Should have 4 trades: 2 buys and 2 sells
        assert result.total_trades == 4

    def test_buy_and_hold_calculated(self, backtester, sample_signals_data):
        """Test that buy-and-hold benchmark is calculated."""
        result = backtester.run_backtest(sample_signals_data)

        # Price doubles, so buy-and-hold should roughly double
        assert result.buyhold_final_value > result.initial_investment
        assert result.buyhold_return_pct > 0

    def test_portfolio_history_populated(self, backtester, sample_signals_data):
        """Test that portfolio history is populated."""
        result = backtester.run_backtest(sample_signals_data)

        assert not result.portfolio_history.empty
        assert "date" in result.portfolio_history.columns
        assert "portfolio_value" in result.portfolio_history.columns
        assert "buyhold_value" in result.portfolio_history.columns

    def test_all_buy_signals(self, backtester):
        """Test backtest with all buy signals."""
        dates = pd.date_range(start="2023-01-01", periods=10, freq="D")
        df = pd.DataFrame({
            "date": dates,
            "price": [100, 110, 120, 130, 140, 150, 160, 170, 180, 190],
            "action": ["BUY"] * 10,
        })

        result = backtester.run_backtest(df)

        # Should only have 1 buy (first one)
        assert result.total_trades == 1
        assert result.trades[0].action == "BUY"

    def test_all_sell_signals(self, backtester):
        """Test backtest with all sell signals (no trades since starting in cash)."""
        dates = pd.date_range(start="2023-01-01", periods=10, freq="D")
        df = pd.DataFrame({
            "date": dates,
            "price": [100, 90, 80, 70, 60, 50, 40, 30, 20, 10],
            "action": ["SELL"] * 10,
        })

        result = backtester.run_backtest(df)

        # Should have no trades (can't sell when in cash)
        assert result.total_trades == 0

    def test_all_hold_signals(self, backtester):
        """Test backtest with all hold signals."""
        dates = pd.date_range(start="2023-01-01", periods=10, freq="D")
        df = pd.DataFrame({
            "date": dates,
            "price": [100] * 10,
            "action": ["HOLD"] * 10,
        })

        result = backtester.run_backtest(df)

        # Should have no trades
        assert result.total_trades == 0
        # Final value should equal initial (stayed in cash)
        assert result.final_value == result.initial_investment


class TestBacktestMetrics:
    """Tests for BacktestMetrics class."""

    @pytest.fixture
    def metrics_calculator(self):
        return BacktestMetrics()

    @pytest.fixture
    def sample_portfolio_history(self):
        """Create sample portfolio history for testing."""
        dates = pd.date_range(start="2023-01-01", periods=365, freq="D")
        # Portfolio that grows 50% over the year
        values = np.linspace(100, 150, 365)
        buyhold = np.linspace(100, 200, 365)

        return pd.DataFrame({
            "date": dates,
            "portfolio_value": values,
            "buyhold_value": buyhold,
            "position": ["ETH"] * 365,
        })

    @pytest.fixture
    def sample_trades(self):
        """Create sample trades for testing."""
        return [
            Trade(
                date=datetime(2023, 1, 10),
                action="BUY",
                price=100,
                eth_amount=1.0,
                usd_value=100,
            ),
            Trade(
                date=datetime(2023, 3, 15),
                action="SELL",
                price=120,  # Winning trade
                eth_amount=1.0,
                usd_value=120,
            ),
            Trade(
                date=datetime(2023, 5, 1),
                action="BUY",
                price=110,
                eth_amount=1.09,
                usd_value=120,
            ),
            Trade(
                date=datetime(2023, 7, 1),
                action="SELL",
                price=100,  # Losing trade
                eth_amount=1.09,
                usd_value=109,
            ),
        ]

    def test_calculate_all_metrics_returns_performance_metrics(
        self,
        metrics_calculator,
        sample_portfolio_history,
        sample_trades,
    ):
        """Test that calculate_all_metrics returns PerformanceMetrics."""
        metrics = metrics_calculator.calculate_all_metrics(
            sample_portfolio_history,
            sample_trades,
            initial_investment=100,
        )

        assert isinstance(metrics, PerformanceMetrics)

    def test_total_return_calculation(
        self,
        metrics_calculator,
        sample_portfolio_history,
        sample_trades,
    ):
        """Test total return is calculated correctly."""
        metrics = metrics_calculator.calculate_all_metrics(
            sample_portfolio_history,
            sample_trades,
            initial_investment=100,
        )

        # Portfolio grew from 100 to 150 = 50% return
        assert metrics.total_return_pct == 50.0

    def test_max_drawdown_calculation(self, metrics_calculator):
        """Test max drawdown calculation."""
        # Portfolio that peaks at 200 then falls to 100
        values = pd.Series([100, 150, 200, 150, 100, 120])
        drawdown = metrics_calculator._calculate_max_drawdown(values)

        # Max drawdown should be 50% (200 -> 100)
        assert drawdown == 50.0

    def test_win_rate_calculation(self, metrics_calculator, sample_trades):
        """Test win rate calculation."""
        win_rate = metrics_calculator._calculate_win_rate(sample_trades)

        # 1 winning trade, 1 losing trade = 50%
        assert win_rate == 50.0

    def test_market_exposure(
        self,
        metrics_calculator,
        sample_portfolio_history,
        sample_trades,
    ):
        """Test market exposure calculation."""
        metrics = metrics_calculator.calculate_all_metrics(
            sample_portfolio_history,
            sample_trades,
            initial_investment=100,
        )

        # All days in ETH = 100% exposure
        assert metrics.market_exposure_pct == 100.0


class TestTradingAction:
    """Tests for TradingAction enum."""

    def test_trading_action_values(self):
        assert TradingAction.BUY.value == "BUY"
        assert TradingAction.HOLD.value == "HOLD"
        assert TradingAction.SELL.value == "SELL"


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        simulator = SignalSimulator()
        empty_df = pd.DataFrame(columns=["date", "price", "volume"])

        result = simulator.simulate_signals(empty_df)
        assert len(result) == 0

    def test_single_day_data(self):
        """Test handling of single day of data."""
        simulator = SignalSimulator()
        single_day = pd.DataFrame({
            "date": [pd.Timestamp("2023-01-01")],
            "price": [1500],
            "volume": [1e9],
        })

        result = simulator.simulate_signals(single_day)
        assert len(result) == 1

    def test_extreme_price_movements(self):
        """Test handling of extreme price movements."""
        simulator = SignalSimulator()
        dates = pd.date_range(start="2023-01-01", periods=30, freq="D")

        # Price drops 90% then recovers
        prices = [1000] * 10 + [100] * 10 + [1000] * 10

        df = pd.DataFrame({
            "date": dates,
            "price": prices,
            "volume": [1e9] * 30,
        })

        result = simulator.simulate_signals(df)

        # Should still have bounded EFI values
        assert result["efi_value"].min() >= -5
        assert result["efi_value"].max() <= 5
