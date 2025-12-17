"""Chart generation for backtest results."""

import logging
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np

from source.config import settings
from source.backtest.backtester import BacktestResult

logger = logging.getLogger(__name__)

# Use non-interactive backend for CLI
plt.switch_backend('Agg')


class BacktestVisualizer:
    """
    Generates charts for backtest results.

    Creates three main visualizations:
    1. ETH price with buy/sell markers
    2. EFI value over time with regime bands
    3. Portfolio value vs buy-and-hold comparison
    """

    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir or settings.backtest.charts_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Style configuration
        plt.style.use('seaborn-v0_8-whitegrid')
        self.colors = {
            "price": "#2E86AB",
            "portfolio": "#28A745",
            "buyhold": "#6C757D",
            "buy_marker": "#28A745",
            "sell_marker": "#DC3545",
            "efi_positive": "#28A745",
            "efi_negative": "#DC3545",
            "efi_neutral": "#FFC107",
        }
        self.regime_colors = {
            "Explosive": "#1B5E20",
            "Constructive": "#4CAF50",
            "Neutral": "#FFC107",
            "Fragile": "#FF9800",
            "Stress": "#D32F2F",
        }

    def generate_all_charts(
        self,
        result: BacktestResult,
        show: bool = False,
    ) -> list[str]:
        """
        Generate all backtest charts.

        Args:
            result: BacktestResult with all data
            show: If True, display charts (not recommended for CLI)

        Returns:
            List of generated file paths
        """
        paths = []

        # Chart 1: Price with signals
        path1 = self.plot_price_with_signals(result)
        paths.append(path1)

        # Chart 2: EFI timeline
        path2 = self.plot_efi_timeline(result)
        paths.append(path2)

        # Chart 3: Portfolio comparison
        path3 = self.plot_portfolio_comparison(result)
        paths.append(path3)

        # Chart 4: Combined dashboard
        path4 = self.plot_dashboard(result)
        paths.append(path4)

        logger.info(f"Generated {len(paths)} charts in {self.output_dir}")
        return paths

    def plot_price_with_signals(self, result: BacktestResult) -> str:
        """
        Plot ETH price with buy/sell markers.

        Args:
            result: BacktestResult

        Returns:
            Path to saved chart
        """
        fig, ax = plt.subplots(figsize=(14, 7))

        df = result.signals_history.copy()
        date_col = "date" if "date" in df.columns else "week_end"

        # Plot price line
        ax.plot(
            df[date_col],
            df["price"],
            color=self.colors["price"],
            linewidth=1.5,
            label="ETH Price",
        )

        # Add buy markers
        buys = df[df["action"] == "BUY"]
        ax.scatter(
            buys[date_col],
            buys["price"],
            color=self.colors["buy_marker"],
            marker="^",
            s=100,
            label="Buy Signal",
            zorder=5,
        )

        # Add sell markers
        sells = df[df["action"] == "SELL"]
        ax.scatter(
            sells[date_col],
            sells["price"],
            color=self.colors["sell_marker"],
            marker="v",
            s=100,
            label="Sell Signal",
            zorder=5,
        )

        ax.set_title("ETH Price with EFI Trading Signals", fontsize=14, fontweight="bold")
        ax.set_xlabel("Date", fontsize=12)
        ax.set_ylabel("Price (USD)", fontsize=12)
        ax.legend(loc="upper left")
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x:,.0f}"))

        # Format x-axis
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        plt.xticks(rotation=45)

        plt.tight_layout()

        filepath = self.output_dir / "price_with_signals.png"
        plt.savefig(filepath, dpi=150, bbox_inches="tight")
        plt.close()

        return str(filepath)

    def plot_efi_timeline(self, result: BacktestResult) -> str:
        """
        Plot EFI value over time with regime bands.

        Args:
            result: BacktestResult

        Returns:
            Path to saved chart
        """
        fig, ax = plt.subplots(figsize=(14, 7))

        df = result.signals_history.copy()
        date_col = "date" if "date" in df.columns else "week_end"

        # Create color array based on EFI value
        colors = []
        for efi in df["efi_value"]:
            if efi >= 2:
                colors.append(self.colors["efi_positive"])
            elif efi <= -2:
                colors.append(self.colors["efi_negative"])
            else:
                colors.append(self.colors["efi_neutral"])

        # Plot EFI as bar chart
        ax.bar(
            df[date_col],
            df["efi_value"],
            color=colors,
            alpha=0.7,
            width=1,
        )

        # Add regime bands
        ax.axhspan(4, 5.5, alpha=0.1, color=self.regime_colors["Explosive"], label="Explosive")
        ax.axhspan(2, 4, alpha=0.1, color=self.regime_colors["Constructive"], label="Constructive")
        ax.axhspan(-1, 2, alpha=0.1, color=self.regime_colors["Neutral"], label="Neutral")
        ax.axhspan(-3, -1, alpha=0.1, color=self.regime_colors["Fragile"], label="Fragile")
        ax.axhspan(-5.5, -3, alpha=0.1, color=self.regime_colors["Stress"], label="Stress")

        # Add threshold lines
        ax.axhline(y=2, color="green", linestyle="--", alpha=0.5, label="Buy Threshold")
        ax.axhline(y=-2, color="red", linestyle="--", alpha=0.5, label="Sell Threshold")
        ax.axhline(y=0, color="gray", linestyle="-", alpha=0.3)

        ax.set_title("EFI Value Over Time with Regime Classification", fontsize=14, fontweight="bold")
        ax.set_xlabel("Date", fontsize=12)
        ax.set_ylabel("EFI Value", fontsize=12)
        ax.set_ylim(-6, 6)
        ax.legend(loc="upper right", fontsize=8)

        # Format x-axis
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        plt.xticks(rotation=45)

        plt.tight_layout()

        filepath = self.output_dir / "efi_timeline.png"
        plt.savefig(filepath, dpi=150, bbox_inches="tight")
        plt.close()

        return str(filepath)

    def plot_portfolio_comparison(self, result: BacktestResult) -> str:
        """
        Plot portfolio value vs buy-and-hold benchmark.

        Args:
            result: BacktestResult

        Returns:
            Path to saved chart
        """
        fig, ax = plt.subplots(figsize=(14, 7))

        df = result.portfolio_history.copy()

        # Plot portfolio value
        ax.plot(
            df["date"],
            df["portfolio_value"],
            color=self.colors["portfolio"],
            linewidth=2,
            label=f"EFI Strategy (${result.final_value:,.2f})",
        )

        # Plot buy-and-hold
        ax.plot(
            df["date"],
            df["buyhold_value"],
            color=self.colors["buyhold"],
            linewidth=2,
            linestyle="--",
            label=f"Buy & Hold (${result.buyhold_final_value:,.2f})",
        )

        # Add initial investment line
        ax.axhline(
            y=result.initial_investment,
            color="black",
            linestyle=":",
            alpha=0.5,
            label=f"Initial (${result.initial_investment:,.2f})",
        )

        ax.set_title(
            f"Portfolio Performance: EFI Strategy vs Buy-and-Hold\n"
            f"Strategy: {result.total_return_pct:+.1f}% | B&H: {result.buyhold_return_pct:+.1f}% | "
            f"Outperformance: {result.outperformance_pct:+.1f}%",
            fontsize=14,
            fontweight="bold",
        )
        ax.set_xlabel("Date", fontsize=12)
        ax.set_ylabel("Portfolio Value (USD)", fontsize=12)
        ax.legend(loc="upper left")
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x:,.0f}"))

        # Format x-axis
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        plt.xticks(rotation=45)

        plt.tight_layout()

        filepath = self.output_dir / "portfolio_comparison.png"
        plt.savefig(filepath, dpi=150, bbox_inches="tight")
        plt.close()

        return str(filepath)

    def plot_dashboard(self, result: BacktestResult) -> str:
        """
        Create a combined dashboard with all charts.

        Args:
            result: BacktestResult

        Returns:
            Path to saved chart
        """
        fig = plt.figure(figsize=(16, 12))

        # Create grid
        gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.2)

        df_signals = result.signals_history.copy()
        df_portfolio = result.portfolio_history.copy()
        date_col = "date" if "date" in df_signals.columns else "week_end"

        # Plot 1: Price with signals (top left)
        ax1 = fig.add_subplot(gs[0, 0])
        ax1.plot(df_signals[date_col], df_signals["price"], color=self.colors["price"], linewidth=1)
        buys = df_signals[df_signals["action"] == "BUY"]
        sells = df_signals[df_signals["action"] == "SELL"]
        ax1.scatter(buys[date_col], buys["price"], color=self.colors["buy_marker"], marker="^", s=50)
        ax1.scatter(sells[date_col], sells["price"], color=self.colors["sell_marker"], marker="v", s=50)
        ax1.set_title("ETH Price with Signals", fontweight="bold")
        ax1.set_ylabel("Price (USD)")
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x:,.0f}"))

        # Plot 2: Portfolio comparison (top right)
        ax2 = fig.add_subplot(gs[0, 1])
        ax2.plot(df_portfolio["date"], df_portfolio["portfolio_value"], color=self.colors["portfolio"], linewidth=1.5, label="Strategy")
        ax2.plot(df_portfolio["date"], df_portfolio["buyhold_value"], color=self.colors["buyhold"], linewidth=1.5, linestyle="--", label="B&H")
        ax2.set_title("Portfolio Value Comparison", fontweight="bold")
        ax2.set_ylabel("Value (USD)")
        ax2.legend(loc="upper left", fontsize=8)
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x:,.0f}"))

        # Plot 3: EFI timeline (middle, full width)
        ax3 = fig.add_subplot(gs[1, :])
        colors = [self.colors["efi_positive"] if e >= 2 else self.colors["efi_negative"] if e <= -2 else self.colors["efi_neutral"] for e in df_signals["efi_value"]]
        ax3.bar(df_signals[date_col], df_signals["efi_value"], color=colors, alpha=0.7, width=1)
        ax3.axhline(y=2, color="green", linestyle="--", alpha=0.5)
        ax3.axhline(y=-2, color="red", linestyle="--", alpha=0.5)
        ax3.set_title("EFI Value Over Time", fontweight="bold")
        ax3.set_ylabel("EFI")
        ax3.set_ylim(-6, 6)

        # Plot 4: Signal components breakdown (bottom left)
        ax4 = fig.add_subplot(gs[2, 0])
        signal_cols = ["s1_value", "s2_value", "s3_value", "s4_value", "s5_value"]
        signal_means = [df_signals[col].mean() for col in signal_cols]
        signal_labels = ["S1: Supply", "S2: Staking", "S3: ETF", "S4: Exchange", "S5: Leverage"]
        bar_colors = [self.colors["efi_positive"] if m > 0 else self.colors["efi_negative"] if m < 0 else self.colors["efi_neutral"] for m in signal_means]
        ax4.barh(signal_labels, signal_means, color=bar_colors, alpha=0.7)
        ax4.axvline(x=0, color="gray", linestyle="-", alpha=0.5)
        ax4.set_title("Average Signal Components", fontweight="bold")
        ax4.set_xlabel("Average Value")
        ax4.set_xlim(-1, 1)

        # Plot 5: Performance summary (bottom right)
        ax5 = fig.add_subplot(gs[2, 1])
        ax5.axis("off")
        summary_text = f"""
PERFORMANCE SUMMARY
═══════════════════════════════════

Initial Investment:  ${result.initial_investment:,.2f}
Final Value:         ${result.final_value:,.2f}

Strategy Return:     {result.total_return_pct:+.1f}%
Buy & Hold Return:   {result.buyhold_return_pct:+.1f}%
Outperformance:      {result.outperformance_pct:+.1f}%

Total Trades:        {result.total_trades}
Win Rate:            {result.win_rate:.1f}%

Period: {result.start_date[:10]} to {result.end_date[:10]}
"""
        ax5.text(0.1, 0.5, summary_text, fontfamily="monospace", fontsize=10, verticalalignment="center", transform=ax5.transAxes)

        plt.suptitle("EFI Backtest Dashboard", fontsize=16, fontweight="bold", y=0.98)

        filepath = self.output_dir / "backtest_dashboard.png"
        plt.savefig(filepath, dpi=150, bbox_inches="tight")
        plt.close()

        return str(filepath)

    def plot_drawdown(self, result: BacktestResult) -> str:
        """
        Plot drawdown over time.

        Args:
            result: BacktestResult

        Returns:
            Path to saved chart
        """
        fig, ax = plt.subplots(figsize=(14, 5))

        df = result.portfolio_history.copy()

        # Calculate drawdown
        rolling_max = df["portfolio_value"].expanding().max()
        drawdown = (df["portfolio_value"] - rolling_max) / rolling_max * 100

        ax.fill_between(
            df["date"],
            drawdown,
            0,
            color=self.colors["efi_negative"],
            alpha=0.5,
        )
        ax.plot(df["date"], drawdown, color=self.colors["efi_negative"], linewidth=1)

        ax.set_title("Portfolio Drawdown Over Time", fontsize=14, fontweight="bold")
        ax.set_xlabel("Date", fontsize=12)
        ax.set_ylabel("Drawdown (%)", fontsize=12)

        # Format x-axis
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        plt.xticks(rotation=45)

        plt.tight_layout()

        filepath = self.output_dir / "drawdown.png"
        plt.savefig(filepath, dpi=150, bbox_inches="tight")
        plt.close()

        return str(filepath)
