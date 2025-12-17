"""Core backtest engine with portfolio simulation."""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import pandas as pd
import numpy as np

from source.config import settings
from source.backtest.signal_simulator import TradingAction

logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """Represents a single trade."""
    date: datetime
    action: str  # BUY or SELL
    price: float
    eth_amount: float
    usd_value: float


@dataclass
class BacktestResult:
    """Complete backtest results."""
    start_date: str
    end_date: str
    initial_investment: float

    # Strategy performance
    final_value: float
    total_return_pct: float
    total_trades: int

    # Buy-and-hold benchmark
    buyhold_final_value: float
    buyhold_return_pct: float

    # Fields with defaults must come after fields without
    trades: list[Trade] = field(default_factory=list)
    portfolio_history: pd.DataFrame = field(default_factory=pd.DataFrame)
    signals_history: pd.DataFrame = field(default_factory=pd.DataFrame)
    outperformance_pct: float = 0.0
    win_rate: float = 0.0


class Backtester:
    """
    Portfolio backtester that simulates trading based on EFI signals.

    Trading Logic:
    - BUY: Invest all cash into ETH when EFI >= +2
    - SELL: Convert all ETH to cash when EFI <= -2
    - HOLD: Maintain current position when -1 <= EFI <= +1
    """

    def __init__(self, initial_investment: float = 100.0):
        self.initial_investment = initial_investment
        self.config = settings.backtest

    def run_backtest(
        self,
        signals_df: pd.DataFrame,
        use_weekly: bool = True,
    ) -> BacktestResult:
        """
        Run backtest simulation.

        Args:
            signals_df: DataFrame with date, price, efi_value, action columns
            use_weekly: If True, use weekly signals for trading decisions

        Returns:
            BacktestResult with full performance analysis
        """
        df = signals_df.copy()
        df = df.sort_values("date" if "date" in df.columns else "week_end")
        df = df.reset_index(drop=True)

        # Ensure date column exists
        date_col = "date" if "date" in df.columns else "week_end"

        # Initialize portfolio state
        cash = self.initial_investment
        eth_holdings = 0.0
        trades: list[Trade] = []

        # Track portfolio value over time
        portfolio_values = []
        buyhold_values = []

        # Buy-and-hold: buy at start price
        start_price = df.iloc[0]["price"]
        buyhold_eth = self.initial_investment / start_price

        # Track current position
        position = "CASH"  # CASH or ETH

        for idx, row in df.iterrows():
            current_price = row["price"]
            current_date = row[date_col]
            action = row.get("action", "HOLD")

            # Calculate current portfolio value
            if position == "ETH":
                portfolio_value = eth_holdings * current_price
            else:
                portfolio_value = cash

            # Buy-and-hold value
            buyhold_value = buyhold_eth * current_price

            # Execute trading logic
            if action == TradingAction.BUY.value and position == "CASH":
                # Buy ETH with all cash
                eth_holdings = cash / current_price
                trade = Trade(
                    date=current_date,
                    action="BUY",
                    price=current_price,
                    eth_amount=eth_holdings,
                    usd_value=cash,
                )
                trades.append(trade)
                cash = 0.0
                position = "ETH"
                logger.debug(f"BUY at {current_date}: {eth_holdings:.4f} ETH @ ${current_price:.2f}")

            elif action == TradingAction.SELL.value and position == "ETH":
                # Sell all ETH
                cash = eth_holdings * current_price
                trade = Trade(
                    date=current_date,
                    action="SELL",
                    price=current_price,
                    eth_amount=eth_holdings,
                    usd_value=cash,
                )
                trades.append(trade)
                eth_holdings = 0.0
                position = "CASH"
                logger.debug(f"SELL at {current_date}: ${cash:.2f} @ ${current_price:.2f}")

            # Record values
            portfolio_values.append({
                "date": current_date,
                "portfolio_value": portfolio_value,
                "position": position,
                "eth_holdings": eth_holdings,
                "cash": cash,
            })
            buyhold_values.append({
                "date": current_date,
                "buyhold_value": buyhold_value,
            })

        # Final portfolio value
        end_price = df.iloc[-1]["price"]
        if position == "ETH":
            final_value = eth_holdings * end_price
        else:
            final_value = cash

        buyhold_final = buyhold_eth * end_price

        # Calculate returns
        total_return = (final_value - self.initial_investment) / self.initial_investment * 100
        buyhold_return = (buyhold_final - self.initial_investment) / self.initial_investment * 100
        outperformance = total_return - buyhold_return

        # Calculate win rate
        win_rate = self._calculate_win_rate(trades)

        # Build result DataFrames
        portfolio_history = pd.DataFrame(portfolio_values)
        portfolio_history = portfolio_history.merge(
            pd.DataFrame(buyhold_values),
            on="date",
        )

        result = BacktestResult(
            start_date=str(df.iloc[0][date_col]),
            end_date=str(df.iloc[-1][date_col]),
            initial_investment=self.initial_investment,
            final_value=final_value,
            total_return_pct=total_return,
            total_trades=len(trades),
            trades=trades,
            buyhold_final_value=buyhold_final,
            buyhold_return_pct=buyhold_return,
            portfolio_history=portfolio_history,
            signals_history=df,
            outperformance_pct=outperformance,
            win_rate=win_rate,
        )

        logger.info(f"Backtest complete: {len(trades)} trades, {total_return:.2f}% return")
        return result

    def _calculate_win_rate(self, trades: list[Trade]) -> float:
        """
        Calculate win rate from trades.

        A "win" is when a sell happens at a higher price than the preceding buy.
        """
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

        if total_pairs == 0:
            return 0.0

        return wins / total_pairs * 100

    def run_backtest_with_initial_position(
        self,
        signals_df: pd.DataFrame,
        start_in_eth: bool = True,
    ) -> BacktestResult:
        """
        Run backtest starting with a position.

        Args:
            signals_df: DataFrame with signals
            start_in_eth: If True, start fully invested in ETH

        Returns:
            BacktestResult
        """
        df = signals_df.copy()
        df = df.sort_values("date" if "date" in df.columns else "week_end")
        df = df.reset_index(drop=True)

        date_col = "date" if "date" in df.columns else "week_end"

        start_price = df.iloc[0]["price"]

        if start_in_eth:
            cash = 0.0
            eth_holdings = self.initial_investment / start_price
            position = "ETH"
        else:
            cash = self.initial_investment
            eth_holdings = 0.0
            position = "CASH"

        trades: list[Trade] = []
        portfolio_values = []
        buyhold_values = []

        buyhold_eth = self.initial_investment / start_price

        for idx, row in df.iterrows():
            current_price = row["price"]
            current_date = row[date_col]
            action = row.get("action", "HOLD")

            if position == "ETH":
                portfolio_value = eth_holdings * current_price
            else:
                portfolio_value = cash

            buyhold_value = buyhold_eth * current_price

            if action == TradingAction.BUY.value and position == "CASH":
                eth_holdings = cash / current_price
                trade = Trade(
                    date=current_date,
                    action="BUY",
                    price=current_price,
                    eth_amount=eth_holdings,
                    usd_value=cash,
                )
                trades.append(trade)
                cash = 0.0
                position = "ETH"

            elif action == TradingAction.SELL.value and position == "ETH":
                cash = eth_holdings * current_price
                trade = Trade(
                    date=current_date,
                    action="SELL",
                    price=current_price,
                    eth_amount=eth_holdings,
                    usd_value=cash,
                )
                trades.append(trade)
                eth_holdings = 0.0
                position = "CASH"

            portfolio_values.append({
                "date": current_date,
                "portfolio_value": portfolio_value,
                "position": position,
                "eth_holdings": eth_holdings,
                "cash": cash,
            })
            buyhold_values.append({
                "date": current_date,
                "buyhold_value": buyhold_value,
            })

        end_price = df.iloc[-1]["price"]
        if position == "ETH":
            final_value = eth_holdings * end_price
        else:
            final_value = cash

        buyhold_final = buyhold_eth * end_price

        total_return = (final_value - self.initial_investment) / self.initial_investment * 100
        buyhold_return = (buyhold_final - self.initial_investment) / self.initial_investment * 100
        outperformance = total_return - buyhold_return
        win_rate = self._calculate_win_rate(trades)

        portfolio_history = pd.DataFrame(portfolio_values)
        portfolio_history = portfolio_history.merge(
            pd.DataFrame(buyhold_values),
            on="date",
        )

        return BacktestResult(
            start_date=str(df.iloc[0][date_col]),
            end_date=str(df.iloc[-1][date_col]),
            initial_investment=self.initial_investment,
            final_value=final_value,
            total_return_pct=total_return,
            total_trades=len(trades),
            trades=trades,
            buyhold_final_value=buyhold_final,
            buyhold_return_pct=buyhold_return,
            portfolio_history=portfolio_history,
            signals_history=df,
            outperformance_pct=outperformance,
            win_rate=win_rate,
        )
