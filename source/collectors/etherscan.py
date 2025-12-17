"""Etherscan collector for ETH supply and burn data."""

from typing import Any, Optional

from source.config import settings
from source.collectors.base import BaseCollector


class EtherscanCollector(BaseCollector):
    """Collector for Etherscan API - ETH supply and burn data."""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            base_url=settings.api.etherscan_base_url,
            api_key=api_key or settings.api.etherscan_api_key,
            rate_limit_rpm=settings.etherscan_rps * 60,  # Convert RPS to RPM
        )

    async def fetch(self) -> dict[str, Any]:
        """Fetch ETH supply data from Etherscan."""
        # Fetch total supply
        supply_data = await self._get_eth_supply()
        # Fetch ETH2 staking info
        eth2_data = await self._get_eth2_supply()

        return {
            "supply": supply_data,
            "eth2": eth2_data,
        }

    async def _get_eth_supply(self) -> dict[str, Any]:
        """Get current ETH supply."""
        params = {
            "module": "stats",
            "action": "ethsupply2",
        }
        if self.api_key:
            params["apikey"] = self.api_key

        return await self._request("", params=params)

    async def _get_eth2_supply(self) -> dict[str, Any]:
        """Get ETH2 staking supply info."""
        params = {
            "module": "stats",
            "action": "ethsupply2",
        }
        if self.api_key:
            params["apikey"] = self.api_key

        return await self._request("", params=params)

    def parse(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """Parse Etherscan response into structured data."""
        supply_result = raw_data.get("supply", {}).get("result", {})

        # ethsupply2 returns detailed breakdown
        # Values are in Wei, convert to ETH
        wei_to_eth = 1e18

        if isinstance(supply_result, dict):
            eth_supply = float(supply_result.get("EthSupply", 0)) / wei_to_eth
            eth2_staking = float(supply_result.get("Eth2Staking", 0)) / wei_to_eth
            burnt_fees = float(supply_result.get("BurntFees", 0)) / wei_to_eth
        else:
            # Fallback for simple ethsupply response
            eth_supply = float(supply_result) / wei_to_eth if supply_result else 0
            eth2_staking = 0
            burnt_fees = 0

        return {
            "total_supply_eth": eth_supply,
            "eth2_staking_eth": eth2_staking,
            "total_burnt_eth": burnt_fees,
        }

    def validate(self, data: dict[str, Any]) -> bool:
        """Validate supply data."""
        return data.get("total_supply_eth", 0) > 0

    async def get_daily_block_rewards(self, days: int = 7) -> list[dict[str, Any]]:
        """Get daily block rewards for emission calculation."""
        # Note: This would require Etherscan Pro API or alternative source
        # For now, use estimated values
        avg_daily_emission = 1700  # Approximate ETH per day post-merge

        return [{"date": f"day_{i}", "emission_eth": avg_daily_emission} for i in range(days)]
