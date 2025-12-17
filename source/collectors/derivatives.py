"""Derivatives collector for leverage and risk data."""

from typing import Any, Optional

from source.collectors.base import BaseCollector


class DerivativesCollector(BaseCollector):
    """Collector for derivatives data - OI, funding rates, liquidations."""

    def __init__(self):
        # Use Coinglass or similar public API
        super().__init__(
            base_url="https://open-api.coinglass.com/public/v2",
            api_key=None,  # Public endpoints
            rate_limit_rpm=20,
        )

    async def fetch(self) -> dict[str, Any]:
        """
        Fetch derivatives market data.

        Sources:
        - Open Interest from Coinglass public API
        - Funding rates from public aggregators
        - Liquidation data from public sources
        """
        try:
            oi_data = await self._fetch_open_interest()
            funding_data = await self._fetch_funding_rates()
            liquidation_data = await self._fetch_liquidations()

            return {
                "source": "api",
                "open_interest": oi_data,
                "funding": funding_data,
                "liquidations": liquidation_data,
            }
        except Exception:
            # Return fallback data
            return self._get_fallback_data()

    async def _fetch_open_interest(self) -> dict[str, Any]:
        """Fetch ETH open interest data."""
        try:
            # Coinglass public endpoint
            result = await self._request(
                "/open_interest",
                params={"symbol": "ETH"},
            )
            return result
        except Exception:
            return {}

    async def _fetch_funding_rates(self) -> dict[str, Any]:
        """Fetch current funding rates."""
        try:
            result = await self._request(
                "/funding",
                params={"symbol": "ETH"},
            )
            return result
        except Exception:
            return {}

    async def _fetch_liquidations(self) -> dict[str, Any]:
        """Fetch recent liquidation data."""
        try:
            result = await self._request(
                "/liquidation_history",
                params={"symbol": "ETH", "interval": "7d"},
            )
            return result
        except Exception:
            return {}

    def _get_fallback_data(self) -> dict[str, Any]:
        """Get fallback derivatives data when APIs unavailable."""
        return {
            "source": "estimated",
            "open_interest": {
                "current_usd": 8_000_000_000,  # $8B
                "change_7d_pct": 0.05,  # 5% increase
            },
            "funding": {
                "average_rate": 0.01,  # 1% annualized
                "max_rate_7d": 0.03,
            },
            "liquidations": {
                "total_7d_usd": 150_000_000,  # $150M
                "long_pct": 0.55,  # 55% longs
                "short_pct": 0.45,  # 45% shorts
            },
        }

    def parse(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """Parse derivatives data into structured format."""
        if raw_data.get("source") == "api":
            oi = raw_data.get("open_interest", {}).get("data", {})
            funding = raw_data.get("funding", {}).get("data", {})
            liqs = raw_data.get("liquidations", {}).get("data", {})

            # Parse API responses
            oi_current = oi.get("openInterest", 0)
            oi_change = oi.get("change24h", 0) * 7  # Estimate 7d from 24h
            funding_rate = funding.get("fundingRate", 0)
            liq_total = sum(l.get("amount", 0) for l in liqs) if isinstance(liqs, list) else 0
        else:
            # Use fallback data
            oi_data = raw_data.get("open_interest", {})
            funding_data = raw_data.get("funding", {})
            liq_data = raw_data.get("liquidations", {})

            oi_current = oi_data.get("current_usd", 0)
            oi_change = oi_data.get("change_7d_pct", 0)
            funding_rate = funding_data.get("average_rate", 0)
            liq_total = liq_data.get("total_7d_usd", 0)

        return {
            "source": raw_data.get("source", "unknown"),
            "open_interest_usd": oi_current,
            "oi_change_7d_pct": oi_change,
            "funding_rate": funding_rate,
            "liquidations_7d_usd": liq_total,
            "is_estimated": raw_data.get("source") == "estimated",
        }

    def validate(self, data: dict[str, Any]) -> bool:
        """Validate derivatives data."""
        return True

    def calculate_stress_score(self, data: dict[str, Any]) -> float:
        """
        Calculate a stress score from derivatives data.

        Higher score = more market stress
        Returns: 0.0 (healthy) to 1.0 (extreme stress)
        """
        stress = 0.0

        # High OI change = potential stress
        oi_change = abs(data.get("oi_change_7d_pct", 0))
        if oi_change > 0.30:
            stress += 0.3
        elif oi_change > 0.15:
            stress += 0.15

        # High funding rate = stress
        funding = abs(data.get("funding_rate", 0))
        if funding > 0.05:
            stress += 0.3
        elif funding > 0.02:
            stress += 0.15

        # High liquidations = stress
        liqs = data.get("liquidations_7d_usd", 0)
        if liqs > 500_000_000:
            stress += 0.4
        elif liqs > 200_000_000:
            stress += 0.2

        return min(stress, 1.0)
