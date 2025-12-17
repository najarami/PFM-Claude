"""CLI reporter for EFI results using Rich."""

from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from source.engine.efi_calculator import EFIResult
from source.engine.interpreter import EFIInterpreter, EFIInterpretation


class CLIReporter:
    """
    CLI reporter for displaying EFI results.

    Uses Rich library for formatted tables and colored output.
    """

    def __init__(self):
        self.console = Console()
        self.interpreter = EFIInterpreter()

    def display_result(
        self,
        result: EFIResult,
        previous: Optional[EFIResult] = None,
    ) -> None:
        """
        Display EFI result in the terminal.

        Args:
            result: Current EFI result
            previous: Previous week's result for comparison
        """
        interpretation = self.interpreter.interpret(result)

        # Display header
        self._display_header(result, interpretation)

        # Display signals table
        self._display_signals_table(result)

        # Display interpretation
        self._display_interpretation(interpretation)

        # Display comparison if available
        if previous:
            self._display_comparison(result, previous)

        # Display warnings if any
        if result.errors:
            self._display_warnings(result.errors)

    def _display_header(
        self,
        result: EFIResult,
        interpretation: EFIInterpretation,
    ) -> None:
        """Display the main EFI header."""
        regime_color = self.interpreter.get_regime_color(interpretation.regime)
        emoji = self.interpreter.get_efi_emoji(result.efi_value)

        header_text = Text()
        header_text.append(f"\n{emoji} ETH Flow Index (EFI): ", style="bold")
        header_text.append(f"{result.efi_value:+d}", style=f"bold {regime_color}")
        header_text.append(f"  [{interpretation.regime}]", style=regime_color)

        self.console.print(header_text)
        self.console.print(f"Calculated: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        self.console.print("")

    def _display_signals_table(self, result: EFIResult) -> None:
        """Display table of all signals."""
        table = Table(title="Signal Breakdown", show_header=True)

        table.add_column("Signal", style="cyan", width=15)
        table.add_column("Value", justify="center", width=8)
        table.add_column("Raw", justify="right", width=12)
        table.add_column("Interpretation", width=15)
        table.add_column("Description", width=30)

        signal_descriptions = {
            "S1": "Net Supply Change",
            "S2": "Staking Net Flow",
            "S3": "ETF Demand",
            "S4": "Exchange Flow",
            "S5": "Leverage/Stress",
        }

        for name, signal in result.signals.items():
            # Color based on value
            if signal.value == 1:
                value_style = "green"
                value_str = "+1"
            elif signal.value == -1:
                value_style = "red"
                value_str = "-1"
            else:
                value_style = "yellow"
                value_str = "0"

            table.add_row(
                name,
                Text(value_str, style=value_style),
                f"{signal.raw_value:.2f}",
                signal.interpretation,
                signal_descriptions.get(name, ""),
            )

        self.console.print(table)
        self.console.print("")

    def _display_interpretation(self, interpretation: EFIInterpretation) -> None:
        """Display regime interpretation."""
        regime_color = self.interpreter.get_regime_color(interpretation.regime)

        panel_content = Text()
        panel_content.append(f"Regime: ", style="bold")
        panel_content.append(f"{interpretation.regime}\n", style=f"bold {regime_color}")
        panel_content.append(f"{interpretation.description}\n\n")
        panel_content.append(f"Recommendation: ", style="bold")
        panel_content.append(f"{interpretation.recommendation}\n")
        panel_content.append(f"Risk Level: ", style="bold")

        risk_color = {
            "Low": "green",
            "Medium": "yellow",
            "High": "red",
        }.get(interpretation.risk_level, "white")

        panel_content.append(f"{interpretation.risk_level}", style=risk_color)

        panel = Panel(panel_content, title="Market Interpretation", border_style=regime_color)
        self.console.print(panel)
        self.console.print("")

    def _display_comparison(
        self,
        current: EFIResult,
        previous: EFIResult,
    ) -> None:
        """Display comparison with previous week."""
        comparison = self.interpreter.compare_with_previous(current, previous)

        table = Table(title="Week-over-Week Comparison", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Current", justify="center")
        table.add_column("Previous", justify="center")
        table.add_column("Change", justify="center")

        # EFI row
        change = current.efi_value - previous.efi_value
        if change > 0:
            change_style = "green"
        elif change < 0:
            change_style = "red"
        else:
            change_style = "yellow"

        table.add_row(
            "EFI",
            f"{current.efi_value:+d}",
            f"{previous.efi_value:+d}",
            Text(f"{change:+d}", style=change_style),
        )

        # Signal rows
        for name in current.signals:
            if name in previous.signals:
                curr_val = current.signals[name].value
                prev_val = previous.signals[name].value
                sig_change = curr_val - prev_val

                if sig_change > 0:
                    sig_style = "green"
                elif sig_change < 0:
                    sig_style = "red"
                else:
                    sig_style = "yellow"

                table.add_row(
                    name,
                    f"{curr_val:+d}",
                    f"{prev_val:+d}",
                    Text(f"{sig_change:+d}", style=sig_style),
                )

        self.console.print(table)

        # Trend summary
        trend_text = Text()
        trend_text.append("\nTrend: ", style="bold")
        trend_text.append(comparison["trend"])
        self.console.print(trend_text)
        self.console.print("")

    def _display_warnings(self, errors: list[str]) -> None:
        """Display warning messages for failed data sources."""
        self.console.print(
            Panel(
                "\n".join(f"- {e}" for e in errors),
                title="[yellow]Data Collection Warnings[/yellow]",
                border_style="yellow",
            )
        )
        self.console.print("")

    def display_history(self, history: list[dict], limit: int = 10) -> None:
        """Display historical EFI values."""
        if not history:
            self.console.print("[yellow]No historical data available.[/yellow]")
            return

        table = Table(title=f"EFI History (Last {min(limit, len(history))} entries)")
        table.add_column("Date", style="cyan")
        table.add_column("EFI", justify="center")
        table.add_column("S1", justify="center")
        table.add_column("S2", justify="center")
        table.add_column("S3", justify="center")
        table.add_column("S4", justify="center")
        table.add_column("S5", justify="center")
        table.add_column("Regime", justify="center")

        for entry in history[:limit]:
            efi = entry["efi_value"]
            regime = self.interpreter._classify_regime(efi)
            regime_color = self.interpreter.get_regime_color(regime)

            signals = entry.get("signals", {})

            def get_signal_str(name: str) -> Text:
                val = signals.get(name, {}).get("value", 0)
                if val == 1:
                    return Text("+1", style="green")
                elif val == -1:
                    return Text("-1", style="red")
                return Text("0", style="yellow")

            table.add_row(
                entry["timestamp"][:10],
                Text(f"{efi:+d}", style=regime_color),
                get_signal_str("S1"),
                get_signal_str("S2"),
                get_signal_str("S3"),
                get_signal_str("S4"),
                get_signal_str("S5"),
                Text(regime, style=regime_color),
            )

        self.console.print(table)
