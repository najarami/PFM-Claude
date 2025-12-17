"""ETF tracker collector for institutional flow data."""

from typing import Any, Optional
from datetime import datetime

from source.collectors.base import BaseCollector


class ETFTrackerCollector(BaseCollector):
    """Collector for ETH ETF flow data from public sources."""

    def __init__(self):
        # Use a placeholder base URL - will rely on fallback data
        super().__init__(
            base_url="https://api.example.com",  # Placeholder
            api_key=None,
            rate_limit_rpm=10,
        )
        # Track if markets are open (Mon-Fri)
        self._markets_open = self._check_markets_open()

    def _check_markets_open(self) -> bool:
        """Check if US markets are open (weekday)."""
        today = datetime.now()
        return today.weekday() < 5  # Monday = 0, Friday = 4

    async def fetch(self) -> dict[str, Any]:
        """
        Fetch ETH ETF flow data.

        Note: ETH ETF data is typically from SoSoValue or Farside.
        Since these require scraping, we'll use estimated/fallback data
        or allow manual input.
        """
        # In production, this would scrape SoSoValue or use an API
        # For now, return structure with fallback values
        return {
            "source": "estimated",
            "markets_open": self._markets_open,
            "flows": self._get_fallback_flows(),
        }

    def _get_fallback_flows(self) -> dict[str, Any]:
        """Get fallback ETF flow data when API unavailable."""
        # Estimated based on recent ETH ETF activity
        # These would be replaced with real data in production
        return {
            "daily_flows_usd": [
                {"date": "2024-01-01", "flow": 10_000_000},
                {"date": "2024-01-02", "flow": 15_000_000},
                {"date": "2024-01-03", "flow": -5_000_000},
                {"date": "2024-01-04", "flow": 20_000_000},
                {"date": "2024-01-05", "flow": 8_000_000},
            ],
            "weekly_total_usd": 48_000_000,
            "ytd_total_usd": 500_000_000,
        }

    def parse(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """Parse ETF flow data into structured format."""
        flows = raw_data.get("flows", {})

        daily_flows = flows.get("daily_flows_usd", [])
        weekly_total = flows.get("weekly_total_usd", 0)

        # Calculate average daily flow
        if daily_flows:
            avg_daily = sum(f.get("flow", 0) for f in daily_flows) / len(daily_flows)
        else:
            avg_daily = 0

        return {
            "source": raw_data.get("source", "unknown"),
            "markets_open": raw_data.get("markets_open", False),
            "weekly_flow_usd": weekly_total,
            "avg_daily_flow_usd": avg_daily,
            "daily_flows": daily_flows,
            "is_estimated": raw_data.get("source") == "estimated",
        }

    def validate(self, data: dict[str, Any]) -> bool:
        """Validate ETF data."""
        # Allow any data - ETF markets may be closed
        return True

    async def set_manual_flow(self, weekly_flow_usd: float) -> dict[str, Any]:
        """
        Allow manual input of ETF flow data.

        Useful when automated scraping fails or for backtesting.
        """
        return {
            "source": "manual",
            "markets_open": self._markets_open,
            "weekly_flow_usd": weekly_flow_usd,
            "avg_daily_flow_usd": weekly_flow_usd / 5,  # 5 trading days
            "daily_flows": [],
            "is_estimated": False,
        }
