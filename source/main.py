"""Main CLI entry point for ETH Flow Index."""

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from source.engine.efi_calculator import EFICalculator, EFIResult
from source.engine.interpreter import EFIInterpreter
from source.storage.data_store import DataStore
from source.outputs.cli_reporter import CLIReporter
from source.outputs.json_exporter import JSONExporter
from source.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


console = Console()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="ETH Flow Index (EFI) - Quantitative weekly index measuring ETH supply/demand balance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m source.main --calculate          Calculate current EFI
  python -m source.main --history            Show historical EFI values
  python -m source.main --export json        Export results to JSON
  python -m source.main --export csv         Export results to CSV
  python -m source.main --backtest           Run backtest (2020-present)
  python -m source.main --backtest --start-date 2023-01-01
        """,
    )

    parser.add_argument(
        "--calculate",
        action="store_true",
        help="Calculate current EFI value",
    )

    parser.add_argument(
        "--history",
        action="store_true",
        help="Display historical EFI values",
    )

    parser.add_argument(
        "--export",
        choices=["json", "csv"],
        help="Export results to specified format",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Limit for history display (default: 10)",
    )

    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save result to history",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )

    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress output (only show EFI value)",
    )

    # Backtest arguments
    parser.add_argument(
        "--backtest",
        action="store_true",
        help="Run backtest simulation",
    )

    parser.add_argument(
        "--start-date",
        type=str,
        default=settings.backtest.default_start_date,
        help=f"Backtest start date YYYY-MM-DD (default: {settings.backtest.default_start_date})",
    )

    parser.add_argument(
        "--end-date",
        type=str,
        default=None,
        help="Backtest end date YYYY-MM-DD (default: today)",
    )

    parser.add_argument(
        "--initial-investment",
        type=float,
        default=settings.backtest.default_initial_investment,
        help=f"Initial investment amount (default: ${settings.backtest.default_initial_investment})",
    )

    return parser.parse_args()


async def calculate_efi(
    save: bool = True,
    verbose: bool = False,
) -> EFIResult:
    """
    Calculate the current EFI value.

    Args:
        save: Whether to save result to history
        verbose: Enable verbose logging

    Returns:
        EFIResult with calculated values
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    calculator = EFICalculator()

    try:
        result = await calculator.calculate()

        if save:
            store = DataStore()
            store.save_result(result)
            logger.info("Result saved to history")

        return result

    finally:
        await calculator.close()


def display_result(
    result: EFIResult,
    quiet: bool = False,
) -> None:
    """Display EFI result."""
    if quiet:
        print(result.efi_value)
        return

    reporter = CLIReporter()

    # Try to get previous result for comparison
    store = DataStore()
    previous_data = store.get_previous()

    if previous_data:
        # Reconstruct previous result for comparison
        # This is a simplified comparison - full reconstruction would need more data
        previous = None  # Would need to reconstruct EFIResult from stored data
    else:
        previous = None

    reporter.display_result(result, previous)


def display_history(limit: int = 10) -> None:
    """Display historical EFI values."""
    store = DataStore()
    history = store.get_history(limit=limit)

    reporter = CLIReporter()
    reporter.display_history(history, limit=limit)


def export_results(format: str) -> str:
    """Export results to specified format."""
    store = DataStore()
    history = store.get_history()

    if not history:
        console.print("[yellow]No historical data to export.[/yellow]")
        sys.exit(1)

    if format == "json":
        filepath = store.export_to_json()
    else:
        filepath = store.export_to_csv()

    return filepath


async def run_backtest(
    start_date: str,
    end_date: Optional[str],
    initial_investment: float,
    verbose: bool = False,
) -> None:
    """
    Run backtest simulation.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format (defaults to today)
        initial_investment: Initial investment amount in USD
        verbose: Enable verbose output
    """
    from source.backtest.historical_data import HistoricalDataFetcher
    from source.backtest.signal_simulator import SignalSimulator
    from source.backtest.backtester import Backtester
    from source.backtest.metrics import BacktestMetrics
    from source.backtest.visualizer import BacktestVisualizer

    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    end_date = end_date or datetime.now().strftime("%Y-%m-%d")

    console.print(Panel(
        f"[bold]EFI Backtest Simulation[/bold]\n\n"
        f"Period: {start_date} to {end_date}\n"
        f"Initial Investment: ${initial_investment:,.2f}",
        title="Backtest Configuration",
        border_style="blue",
    ))

    # Step 1: Fetch historical data
    console.print("\n[cyan]Step 1/4:[/cyan] Fetching historical ETH prices...")
    fetcher = HistoricalDataFetcher()
    price_df = await fetcher.fetch_eth_prices(start_date, end_date)
    console.print(f"  Retrieved {len(price_df)} days of price data")

    # Step 2: Simulate EFI signals
    console.print("\n[cyan]Step 2/4:[/cyan] Simulating EFI signals...")
    simulator = SignalSimulator()
    signals_df = simulator.simulate_signals(price_df)
    console.print(f"  Generated signals for {len(signals_df)} days")

    # Show signal distribution
    signal_counts = signals_df["action"].value_counts()
    console.print(f"  Signal distribution: BUY={signal_counts.get('BUY', 0)}, "
                  f"HOLD={signal_counts.get('HOLD', 0)}, SELL={signal_counts.get('SELL', 0)}")

    # Step 3: Run backtest
    console.print("\n[cyan]Step 3/4:[/cyan] Running backtest simulation...")
    backtester = Backtester(initial_investment=initial_investment)
    result = backtester.run_backtest(signals_df)
    console.print(f"  Executed {result.total_trades} trades")

    # Step 4: Generate charts
    console.print("\n[cyan]Step 4/4:[/cyan] Generating charts...")
    visualizer = BacktestVisualizer()
    chart_paths = visualizer.generate_all_charts(result)
    for path in chart_paths:
        console.print(f"  Created: {path}")

    # Calculate detailed metrics
    metrics_calc = BacktestMetrics()
    metrics = metrics_calc.calculate_all_metrics(
        result.portfolio_history,
        result.trades,
        initial_investment,
    )

    # Display results
    console.print("\n")
    _display_backtest_results(result, metrics)

    # Save results to JSON
    results_file = settings.backtest.results_file
    _save_backtest_results(result, metrics, results_file)
    console.print(f"\n[green]Results saved to: {results_file}[/green]")


def _display_backtest_results(result, metrics) -> None:
    """Display backtest results in a formatted table."""
    # Performance summary panel
    if result.outperformance_pct >= 0:
        perf_color = "green"
        perf_emoji = "+"
    else:
        perf_color = "red"
        perf_emoji = ""

    summary = Table(title="Performance Summary", show_header=False, box=None)
    summary.add_column("Metric", style="cyan", width=25)
    summary.add_column("Value", justify="right", width=20)

    summary.add_row("Initial Investment", f"${result.initial_investment:,.2f}")
    summary.add_row("Final Value", f"${result.final_value:,.2f}")
    summary.add_row("", "")
    summary.add_row("Strategy Return", f"[bold]{result.total_return_pct:+.2f}%[/bold]")
    summary.add_row("Buy & Hold Return", f"{result.buyhold_return_pct:+.2f}%")
    summary.add_row(
        "Outperformance",
        f"[{perf_color}]{perf_emoji}{result.outperformance_pct:.2f}%[/{perf_color}]"
    )

    console.print(Panel(summary, border_style="green"))

    # Risk metrics
    risk_table = Table(title="Risk Metrics", show_header=False, box=None)
    risk_table.add_column("Metric", style="cyan", width=25)
    risk_table.add_column("Value", justify="right", width=20)

    risk_table.add_row("Max Drawdown", f"{metrics.max_drawdown_pct:.2f}%")
    risk_table.add_row("Annual Volatility", f"{metrics.volatility_annual:.2f}%")
    risk_table.add_row("Sharpe Ratio", f"{metrics.sharpe_ratio:.2f}")
    risk_table.add_row("Annualized Return", f"{metrics.annualized_return_pct:+.2f}%")

    console.print(Panel(risk_table, border_style="yellow"))

    # Trading stats
    trade_table = Table(title="Trading Statistics", show_header=False, box=None)
    trade_table.add_column("Metric", style="cyan", width=25)
    trade_table.add_column("Value", justify="right", width=20)

    trade_table.add_row("Total Trades", str(result.total_trades))
    trade_table.add_row("Win Rate", f"{metrics.win_rate_pct:.2f}%")
    trade_table.add_row("Avg Trade Return", f"{metrics.avg_trade_return_pct:+.2f}%")
    trade_table.add_row("Market Exposure", f"{metrics.market_exposure_pct:.2f}%")
    trade_table.add_row("Days in Market", f"{metrics.days_in_market} / {metrics.total_days}")

    console.print(Panel(trade_table, border_style="blue"))


def _save_backtest_results(result, metrics, filepath: str) -> None:
    """Save backtest results to JSON file."""
    from pathlib import Path

    data = {
        "backtest_config": {
            "start_date": result.start_date,
            "end_date": result.end_date,
            "initial_investment": result.initial_investment,
        },
        "performance": {
            "final_value": result.final_value,
            "total_return_pct": result.total_return_pct,
            "buyhold_return_pct": result.buyhold_return_pct,
            "outperformance_pct": result.outperformance_pct,
        },
        "risk_metrics": {
            "max_drawdown_pct": metrics.max_drawdown_pct,
            "volatility_annual": metrics.volatility_annual,
            "sharpe_ratio": metrics.sharpe_ratio,
            "annualized_return_pct": metrics.annualized_return_pct,
        },
        "trading_stats": {
            "total_trades": result.total_trades,
            "win_rate_pct": metrics.win_rate_pct,
            "avg_trade_return_pct": metrics.avg_trade_return_pct,
            "market_exposure_pct": metrics.market_exposure_pct,
        },
        "trades": [
            {
                "date": str(t.date),
                "action": t.action,
                "price": t.price,
                "eth_amount": t.eth_amount,
                "usd_value": t.usd_value,
            }
            for t in result.trades
        ],
    }

    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)



async def main() -> int:
    """Main entry point."""
    args = parse_args()

    try:
        if args.calculate:
            console.print("[bold]Calculating ETH Flow Index...[/bold]\n")
            result = await calculate_efi(
                save=not args.no_save,
                verbose=args.verbose,
            )
            display_result(result, quiet=args.quiet)

        elif args.history:
            display_history(limit=args.limit)

        elif args.export:
            filepath = export_results(args.export)
            console.print(f"[green]Exported to: {filepath}[/green]")

        elif args.backtest:
            await run_backtest(
                start_date=args.start_date,
                end_date=args.end_date,
                initial_investment=args.initial_investment,
                verbose=args.verbose,
            )

        else:
            # Default: show help
            console.print("[yellow]No action specified. Use --help for options.[/yellow]")
            console.print("\nQuick start:")
            console.print("  python -m source.main --calculate")
            console.print("  python -m source.main --backtest")
            return 1

        return 0

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user.[/yellow]")
        return 130

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cli() -> None:
    """CLI entry point for package."""
    sys.exit(asyncio.run(main()))


if __name__ == "__main__":
    cli()
