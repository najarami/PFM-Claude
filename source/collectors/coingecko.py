"""CoinGecko collector for ETH price and market data."""

from typing import Any, Optional

from source.config import settings
from source.collectors.base import BaseCollector


class CoinGeckoCollector(BaseCollector):
    """Collector for CoinGecko API - ETH price and market data."""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            base_url=settings.api.coingecko_base_url,
            api_key=api_key or settings.api.coingecko_api_key,
            rate_limit_rpm=settings.coingecko_rpm,
        )

    async def fetch(self) -> dict[str, Any]:
        """Fetch ETH market data from CoinGecko."""
        params = {
            "ids": "ethereum",
            "vs_currencies": "usd",
            "include_market_cap": "true",
            "include_24hr_vol": "true",
            "include_24hr_change": "true",
        }

        # Add API key to params if available (CoinGecko Pro)
        if self.api_key:
            params["x_cg_pro_api_key"] = self.api_key

        return await self._request("/simple/price", params=params)

    def parse(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """Parse CoinGecko response into structured data."""
        eth_data = raw_data.get("ethereum", {})

        return {
            "price_usd": eth_data.get("usd", 0.0),
            "market_cap_usd": eth_data.get("usd_market_cap", 0.0),
            "volume_24h_usd": eth_data.get("usd_24h_vol", 0.0),
            "price_change_24h_pct": eth_data.get("usd_24h_change", 0.0),
        }

    def validate(self, data: dict[str, Any]) -> bool:
        """Validate that we got valid price data."""
        return data.get("price_usd", 0) > 0

    async def get_market_chart(self, days: int = 7) -> dict[str, Any]:
        """Get historical market data for the past N days."""
        params = {
            "vs_currency": "usd",
            "days": str(days),
        }

        if self.api_key:
            params["x_cg_pro_api_key"] = self.api_key

        raw_data = await self._request("/coins/ethereum/market_chart", params=params)

        prices = raw_data.get("prices", [])
        volumes = raw_data.get("total_volumes", [])
        market_caps = raw_data.get("market_caps", [])

        return {
            "prices": [(ts, price) for ts, price in prices],
            "volumes": [(ts, vol) for ts, vol in volumes],
            "market_caps": [(ts, cap) for ts, cap in market_caps],
        }
