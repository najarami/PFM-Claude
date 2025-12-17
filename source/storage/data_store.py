"""Data storage for EFI historical results."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from source.config import settings
from source.engine.efi_calculator import EFIResult


class DataStore:
    """
    Persistent storage for EFI results.

    Stores historical data in JSON format and supports CSV export.
    """

    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir or settings.data_dir)
        self.history_file = self.data_dir / settings.history_file
        self._ensure_data_dir()

    def _ensure_data_dir(self) -> None:
        """Create data directory if it doesn't exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def save_result(self, result: EFIResult) -> None:
        """
        Save an EFI result to history.

        Args:
            result: EFIResult to save
        """
        history = self._load_history()

        # Convert result to serializable format
        entry = self._result_to_dict(result)

        # Add to history
        history.append(entry)

        # Save updated history
        self._save_history(history)

    def _result_to_dict(self, result: EFIResult) -> dict:
        """Convert EFIResult to serializable dictionary."""
        signals_dict = {}
        for name, signal in result.signals.items():
            signals_dict[name] = {
                "value": signal.value,
                "raw_value": signal.raw_value,
                "interpretation": signal.interpretation,
                "details": signal.details,
            }

        return {
            "timestamp": result.timestamp.isoformat(),
            "efi_value": result.efi_value,
            "signals": signals_dict,
            "errors": result.errors,
            "is_partial": result.is_partial,
        }

    def _load_history(self) -> list[dict]:
        """Load history from JSON file."""
        if not self.history_file.exists():
            return []

        try:
            with open(self.history_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def _save_history(self, history: list[dict]) -> None:
        """Save history to JSON file."""
        with open(self.history_file, "w") as f:
            json.dump(history, f, indent=2)

    def get_history(self, limit: Optional[int] = None) -> list[dict]:
        """
        Get historical EFI results.

        Args:
            limit: Maximum number of entries to return (most recent first)

        Returns:
            List of historical entries
        """
        history = self._load_history()

        # Sort by timestamp descending
        history.sort(key=lambda x: x["timestamp"], reverse=True)

        if limit:
            return history[:limit]
        return history

    def get_latest(self) -> Optional[dict]:
        """Get the most recent EFI result."""
        history = self.get_history(limit=1)
        return history[0] if history else None

    def get_previous(self) -> Optional[dict]:
        """Get the second most recent EFI result (previous week)."""
        history = self.get_history(limit=2)
        return history[1] if len(history) > 1 else None

    def export_to_csv(self, filepath: Optional[str] = None) -> str:
        """
        Export history to CSV file.

        Args:
            filepath: Output file path. Defaults to data_dir/efi_history.csv

        Returns:
            Path to created CSV file
        """
        history = self._load_history()

        if not history:
            raise ValueError("No history data to export")

        # Flatten data for CSV
        rows = []
        for entry in history:
            row = {
                "timestamp": entry["timestamp"],
                "efi_value": entry["efi_value"],
                "is_partial": entry.get("is_partial", False),
            }

            # Add individual signal values
            for signal_name, signal_data in entry.get("signals", {}).items():
                row[f"{signal_name}_value"] = signal_data.get("value", 0)
                row[f"{signal_name}_raw"] = signal_data.get("raw_value", 0)

            rows.append(row)

        df = pd.DataFrame(rows)

        # Set output path
        output_path = filepath or str(self.data_dir / "efi_history.csv")

        df.to_csv(output_path, index=False)
        return output_path

    def export_to_json(self, filepath: Optional[str] = None) -> str:
        """
        Export history to JSON file.

        Args:
            filepath: Output file path

        Returns:
            Path to created JSON file
        """
        history = self._load_history()

        output_path = filepath or str(self.data_dir / "efi_export.json")

        with open(output_path, "w") as f:
            json.dump(history, f, indent=2)

        return output_path

    def clear_history(self) -> None:
        """Clear all historical data."""
        if self.history_file.exists():
            self.history_file.unlink()

    def get_trend(self, periods: int = 4) -> dict:
        """
        Calculate EFI trend over recent periods.

        Args:
            periods: Number of periods to analyze

        Returns:
            Dict with trend analysis
        """
        history = self.get_history(limit=periods)

        if len(history) < 2:
            return {"trend": "Insufficient data", "change": 0}

        values = [h["efi_value"] for h in history]

        # Calculate average change
        changes = [values[i] - values[i + 1] for i in range(len(values) - 1)]
        avg_change = sum(changes) / len(changes)

        if avg_change > 0.5:
            trend = "Improving"
        elif avg_change < -0.5:
            trend = "Deteriorating"
        else:
            trend = "Stable"

        return {
            "trend": trend,
            "average_change": round(avg_change, 2),
            "current": values[0],
            "oldest": values[-1],
            "total_change": values[0] - values[-1],
        }
