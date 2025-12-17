"""JSON/CSV exporter for EFI results."""

import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Optional, Literal

from source.engine.efi_calculator import EFIResult
from source.engine.interpreter import EFIInterpreter


class JSONExporter:
    """
    Exporter for EFI results to JSON and CSV formats.
    """

    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir or "data")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.interpreter = EFIInterpreter()

    def export_result(
        self,
        result: EFIResult,
        format: Literal["json", "csv"] = "json",
        filename: Optional[str] = None,
    ) -> str:
        """
        Export a single EFI result.

        Args:
            result: EFIResult to export
            format: Output format (json or csv)
            filename: Custom filename (without extension)

        Returns:
            Path to exported file
        """
        if format == "json":
            return self._export_json(result, filename)
        else:
            return self._export_csv(result, filename)

    def _export_json(self, result: EFIResult, filename: Optional[str] = None) -> str:
        """Export result to JSON file."""
        interpretation = self.interpreter.interpret(result)

        data = {
            "meta": {
                "generated_at": datetime.now().isoformat(),
                "version": "1.0",
            },
            "result": {
                "timestamp": result.timestamp.isoformat(),
                "efi_value": result.efi_value,
                "regime": interpretation.regime,
                "risk_level": interpretation.risk_level,
                "recommendation": interpretation.recommendation,
                "is_partial": result.is_partial,
            },
            "signals": {},
            "errors": result.errors,
        }

        for name, signal in result.signals.items():
            data["signals"][name] = {
                "value": signal.value,
                "raw_value": signal.raw_value,
                "interpretation": signal.interpretation,
                "name": signal.name,
                "details": signal.details,
            }

        # Generate filename
        if not filename:
            date_str = result.timestamp.strftime("%Y%m%d_%H%M%S")
            filename = f"efi_{date_str}"

        filepath = self.output_dir / f"{filename}.json"

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        return str(filepath)

    def _export_csv(self, result: EFIResult, filename: Optional[str] = None) -> str:
        """Export result to CSV file."""
        interpretation = self.interpreter.interpret(result)

        # Flatten data for CSV
        row = {
            "timestamp": result.timestamp.isoformat(),
            "efi_value": result.efi_value,
            "regime": interpretation.regime,
            "risk_level": interpretation.risk_level,
            "is_partial": result.is_partial,
        }

        # Add individual signal values
        for name, signal in result.signals.items():
            row[f"{name}_value"] = signal.value
            row[f"{name}_raw"] = signal.raw_value
            row[f"{name}_interpretation"] = signal.interpretation

        # Generate filename
        if not filename:
            date_str = result.timestamp.strftime("%Y%m%d_%H%M%S")
            filename = f"efi_{date_str}"

        filepath = self.output_dir / f"{filename}.csv"

        # Write CSV
        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=row.keys())
            writer.writeheader()
            writer.writerow(row)

        return str(filepath)

    def export_batch(
        self,
        results: list[EFIResult],
        format: Literal["json", "csv"] = "json",
        filename: Optional[str] = None,
    ) -> str:
        """
        Export multiple EFI results.

        Args:
            results: List of EFIResults
            format: Output format
            filename: Custom filename

        Returns:
            Path to exported file
        """
        if not filename:
            filename = f"efi_batch_{datetime.now().strftime('%Y%m%d')}"

        if format == "json":
            return self._export_batch_json(results, filename)
        else:
            return self._export_batch_csv(results, filename)

    def _export_batch_json(self, results: list[EFIResult], filename: str) -> str:
        """Export multiple results to JSON."""
        data = {
            "meta": {
                "generated_at": datetime.now().isoformat(),
                "version": "1.0",
                "count": len(results),
            },
            "results": [],
        }

        for result in results:
            interpretation = self.interpreter.interpret(result)
            entry = {
                "timestamp": result.timestamp.isoformat(),
                "efi_value": result.efi_value,
                "regime": interpretation.regime,
                "signals": {
                    name: {
                        "value": s.value,
                        "raw_value": s.raw_value,
                    }
                    for name, s in result.signals.items()
                },
            }
            data["results"].append(entry)

        filepath = self.output_dir / f"{filename}.json"

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        return str(filepath)

    def _export_batch_csv(self, results: list[EFIResult], filename: str) -> str:
        """Export multiple results to CSV."""
        if not results:
            raise ValueError("No results to export")

        # Build rows
        rows = []
        for result in results:
            interpretation = self.interpreter.interpret(result)
            row = {
                "timestamp": result.timestamp.isoformat(),
                "efi_value": result.efi_value,
                "regime": interpretation.regime,
            }

            for name, signal in result.signals.items():
                row[f"{name}_value"] = signal.value
                row[f"{name}_raw"] = signal.raw_value

            rows.append(row)

        filepath = self.output_dir / f"{filename}.csv"

        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

        return str(filepath)

    def get_summary_report(self, result: EFIResult) -> str:
        """
        Generate a text summary report.

        Returns:
            Formatted string report
        """
        interpretation = self.interpreter.interpret(result)

        lines = [
            "=" * 50,
            "ETH FLOW INDEX (EFI) REPORT",
            "=" * 50,
            f"Date: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"EFI Value: {result.efi_value:+d}",
            f"Regime: {interpretation.regime}",
            f"Risk Level: {interpretation.risk_level}",
            "",
            "SIGNAL BREAKDOWN:",
            "-" * 30,
        ]

        for name, signal in result.signals.items():
            lines.append(f"  {name}: {signal.value:+d} ({signal.interpretation})")
            lines.append(f"       Raw: {signal.raw_value:.2f}")

        lines.extend([
            "",
            "INTERPRETATION:",
            "-" * 30,
            interpretation.description,
            "",
            "RECOMMENDATION:",
            interpretation.recommendation,
            "",
            "=" * 50,
        ])

        return "\n".join(lines)
