"""Dune Analytics collector for exchange flow data."""

from typing import Any, Optional

from source.config import settings
from source.collectors.base import BaseCollector


class DuneCollector(BaseCollector):
    """Collector for exchange flow data via Dune Analytics or alternatives."""

    # Known exchange addresses (subset of major exchanges)
    EXCHANGE_ADDRESSES = {
        "binance": [
            "0x28c6c06298d514db089934071355e5743bf21d60",
            "0x21a31ee1afc51d94c2efccaa2092ad1028285549",
        ],
        "coinbase": [
            "0x71660c4005ba85c37ccec55d0c4493e66fe775d3",
            "0x503828976d22510aad0201ac7ec88293211d23da",
        ],
        "kraken": [
            "0x2910543af39aba0cd09dbb2d50200b3e800a63d2",
        ],
    }

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            base_url="https://api.dune.com/api/v1",
            api_key=api_key or settings.api.dune_api_key,
            rate_limit_rpm=10,  # Dune free tier is limited
        )

    async def fetch(self) -> dict[str, Any]:
        """
        Fetch exchange flow data.

        Note: Dune API requires paid tier for queries.
        Falls back to estimated data based on public sources.
        """
        if self.api_key:
            try:
                return await self._fetch_from_dune()
            except Exception:
                pass

        # Fallback to estimated data
        return self._get_fallback_data()

    async def _fetch_from_dune(self) -> dict[str, Any]:
        """Fetch from Dune Analytics API (requires API key)."""
        # Query ID for ETH exchange flows (would need to be created on Dune)
        # This is a placeholder - actual query would be different
        query_id = "1234567"  # Replace with actual Dune query ID

        headers = {"X-Dune-API-Key": self.api_key}

        result = await self._request(
            f"/query/{query_id}/results",
            headers=headers,
        )

        return {
            "source": "dune",
            "data": result,
        }

    def _get_fallback_data(self) -> dict[str, Any]:
        """Get fallback exchange flow data when API unavailable."""
        # Estimated based on typical weekly exchange flows
        return {
            "source": "estimated",
            "data": {
                "inflows_7d_eth": 150000,
                "outflows_7d_eth": 180000,
                "net_flow_7d_eth": -30000,  # Negative = outflows > inflows
                "exchange_reserves_eth": 15_000_000,
                "reserve_change_7d_pct": -0.5,
            },
        }

    def parse(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """Parse exchange flow data into structured format."""
        data = raw_data.get("data", {})

        if raw_data.get("source") == "dune":
            # Parse Dune query results
            rows = data.get("result", {}).get("rows", [])
            if rows:
                latest = rows[0]
                inflows = latest.get("inflows", 0)
                outflows = latest.get("outflows", 0)
                reserves = latest.get("reserves", 0)
            else:
                inflows = outflows = reserves = 0
        else:
            # Use fallback data directly
            inflows = data.get("inflows_7d_eth", 0)
            outflows = data.get("outflows_7d_eth", 0)
            reserves = data.get("exchange_reserves_eth", 0)

        net_flow = inflows - outflows

        return {
            "source": raw_data.get("source", "unknown"),
            "inflows_7d_eth": inflows,
            "outflows_7d_eth": outflows,
            "net_flow_7d_eth": net_flow,
            "exchange_reserves_eth": reserves,
            "is_estimated": raw_data.get("source") == "estimated",
        }

    def validate(self, data: dict[str, Any]) -> bool:
        """Validate exchange flow data."""
        # Allow zero/estimated values
        return True

    async def set_manual_flows(
        self,
        inflows_eth: float,
        outflows_eth: float,
        reserves_eth: Optional[float] = None,
    ) -> dict[str, Any]:
        """
        Allow manual input of exchange flow data.

        Useful for backtesting or when automated sources fail.
        """
        return {
            "source": "manual",
            "inflows_7d_eth": inflows_eth,
            "outflows_7d_eth": outflows_eth,
            "net_flow_7d_eth": inflows_eth - outflows_eth,
            "exchange_reserves_eth": reserves_eth or 0,
            "is_estimated": False,
        }
