"""Performance metrics calculator for backtest results."""

import logging
from dataclasses import dataclass
from typing import Optional

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Complete performance metrics for a backtest."""
    # Returns
    total_return_pct: float
    annualized_return_pct: float
    buyhold_return_pct: float
    outperformance_pct: float

    # Risk metrics
    max_drawdown_pct: float
    volatility_annual: float
    sharpe_ratio: float

    # Trading stats
    total_trades: int
    win_rate_pct: float
    avg_trade_return_pct: float

    # Time metrics
    days_in_market: int
    total_days: int
    market_exposure_pct: float


class BacktestMetrics:
    """
    Calculates comprehensive performance metrics from backtest results.
    """

    def __init__(self, risk_free_rate: float = 0.04):
        """
        Initialize metrics calculator.

        Args:
            risk_free_rate: Annual risk-free rate for Sharpe calculation (default 4%)
        """
        self.risk_free_rate = risk_free_rate

    def calculate_all_metrics(
        self,
        portfolio_history: pd.DataFrame,
        trades: list,
        initial_investment: float,
    ) -> PerformanceMetrics:
        """
        Calculate all performance metrics.

        Args:
            portfolio_history: DataFrame with date, portfolio_value, buyhold_value
            trades: List of Trade objects
            initial_investment: Initial investment amount

        Returns:
            PerformanceMetrics with all calculated values
        """
        df = portfolio_history.copy()

        # Basic returns
        final_value = df["portfolio_value"].iloc[-1]
        buyhold_final = df["buyhold_value"].iloc[-1]

        total_return = (final_value - initial_investment) / initial_investment * 100
        buyhold_return = (buyhold_final - initial_investment) / initial_investment * 100
        outperformance = total_return - buyhold_return

        # Annualized return
        total_days = len(df)
        years = total_days / 365
        if years > 0 and final_value > 0:
            annualized_return = ((final_value / initial_investment) ** (1 / years) - 1) * 100
        else:
            annualized_return = 0.0

        # Max drawdown
        max_drawdown = self._calculate_max_drawdown(df["portfolio_value"])

        # Volatility
        df["daily_return"] = df["portfolio_value"].pct_change()
        daily_vol = df["daily_return"].std()
        annual_vol = daily_vol * np.sqrt(365) if not pd.isna(daily_vol) else 0.0

        # Sharpe ratio
        if annual_vol > 0:
            sharpe = (annualized_return / 100 - self.risk_free_rate) / annual_vol
        else:
            sharpe = 0.0

        # Trading stats
        total_trades = len(trades)
        win_rate = self._calculate_win_rate(trades)
        avg_trade_return = self._calculate_avg_trade_return(trades, initial_investment)

        # Market exposure
        days_in_market = len(df[df["position"] == "ETH"]) if "position" in df.columns else total_days
        market_exposure = days_in_market / total_days * 100 if total_days > 0 else 0

        return PerformanceMetrics(
            total_return_pct=round(total_return, 2),
            annualized_return_pct=round(annualized_return, 2),
            buyhold_return_pct=round(buyhold_return, 2),
            outperformance_pct=round(outperformance, 2),
            max_drawdown_pct=round(max_drawdown, 2),
            volatility_annual=round(annual_vol * 100, 2),
            sharpe_ratio=round(sharpe, 2),
            total_trades=total_trades,
            win_rate_pct=round(win_rate, 2),
            avg_trade_return_pct=round(avg_trade_return, 2),
            days_in_market=days_in_market,
            total_days=total_days,
            market_exposure_pct=round(market_exposure, 2),
        )

    def _calculate_max_drawdown(self, values: pd.Series) -> float:
        """
        Calculate maximum drawdown percentage.

        Max drawdown = largest peak-to-trough decline.
        """
        if len(values) < 2:
            return 0.0

        rolling_max = values.expanding().max()
        drawdowns = (values - rolling_max) / rolling_max * 100

        return abs(drawdowns.min()) if not pd.isna(drawdowns.min()) else 0.0

    def _calculate_win_rate(self, trades: list) -> float:
        """Calculate percentage of winning trades."""
        if len(trades) < 2:
            return 0.0

        wins = 0
        total_pairs = 0
        buy_price = None

        for trade in trades:
            if trade.action == "BUY":
                buy_price = trade.price
            elif trade.action == "SELL" and buy_price is not None:
                total_pairs += 1
                if trade.price > buy_price:
                    wins += 1
                buy_price = None

        return wins / total_pairs * 100 if total_pairs > 0 else 0.0

    def _calculate_avg_trade_return(
        self,
        trades: list,
        initial_investment: float,
    ) -> float:
        """Calculate average return per trade pair."""
        if len(trades) < 2:
            return 0.0

        returns = []
        buy_price = None

        for trade in trades:
            if trade.action == "BUY":
                buy_price = trade.price
            elif trade.action == "SELL" and buy_price is not None:
                trade_return = (trade.price - buy_price) / buy_price * 100
                returns.append(trade_return)
                buy_price = None

        return np.mean(returns) if returns else 0.0

    def generate_summary_report(
        self,
        metrics: PerformanceMetrics,
        initial_investment: float,
        final_value: float,
    ) -> str:
        """
        Generate a formatted summary report.

        Returns:
            Formatted string report
        """
        report = f"""
================================================================================
                         BACKTEST PERFORMANCE REPORT
================================================================================

INVESTMENT SUMMARY
------------------
Initial Investment:     ${initial_investment:,.2f}
Final Value:            ${final_value:,.2f}
Total Return:           {metrics.total_return_pct:+.2f}%
Annualized Return:      {metrics.annualized_return_pct:+.2f}%

BENCHMARK COMPARISON
--------------------
Buy-and-Hold Return:    {metrics.buyhold_return_pct:+.2f}%
Strategy Outperformance:{metrics.outperformance_pct:+.2f}%

RISK METRICS
------------
Max Drawdown:           {metrics.max_drawdown_pct:.2f}%
Annual Volatility:      {metrics.volatility_annual:.2f}%
Sharpe Ratio:           {metrics.sharpe_ratio:.2f}

TRADING STATISTICS
------------------
Total Trades:           {metrics.total_trades}
Win Rate:               {metrics.win_rate_pct:.2f}%
Avg Trade Return:       {metrics.avg_trade_return_pct:+.2f}%
Market Exposure:        {metrics.market_exposure_pct:.2f}%
Days in Market:         {metrics.days_in_market} / {metrics.total_days}

================================================================================
"""
        return report

    def calculate_rolling_metrics(
        self,
        portfolio_history: pd.DataFrame,
        window: int = 30,
    ) -> pd.DataFrame:
        """
        Calculate rolling metrics over time.

        Args:
            portfolio_history: DataFrame with portfolio values
            window: Rolling window in days

        Returns:
            DataFrame with rolling metrics
        """
        df = portfolio_history.copy()

        df["rolling_return"] = df["portfolio_value"].pct_change(window) * 100
        df["rolling_vol"] = df["portfolio_value"].pct_change().rolling(window).std() * np.sqrt(365) * 100
        df["rolling_sharpe"] = (
            df["rolling_return"] / 100 - self.risk_free_rate / 12
        ) / (df["rolling_vol"] / 100)

        return df
