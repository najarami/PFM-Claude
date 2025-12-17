"""Tests for data collectors."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from source.collectors.coingecko import CoinGeckoCollector
from source.collectors.etherscan import EtherscanCollector
from source.collectors.beaconchain import BeaconchainCollector
from source.collectors.etf_tracker import ETFTrackerCollector
from source.collectors.dune import DuneCollector
from source.collectors.derivatives import DerivativesCollector


class TestCoinGeckoCollector:
    """Tests for CoinGecko collector."""

    @pytest.fixture
    def collector(self):
        return CoinGeckoCollector()

    def test_parse_response(self, collector):
        """Test parsing CoinGecko API response."""
        raw_data = {
            "ethereum": {
                "usd": 3500.0,
                "usd_market_cap": 420_000_000_000,
                "usd_24h_vol": 15_000_000_000,
                "usd_24h_change": 2.5,
            }
        }

        result = collector.parse(raw_data)

        assert result["price_usd"] == 3500.0
        assert result["market_cap_usd"] == 420_000_000_000
        assert result["volume_24h_usd"] == 15_000_000_000
        assert result["price_change_24h_pct"] == 2.5

    def test_validate_valid_data(self, collector):
        """Test validation with valid data."""
        data = {"price_usd": 3500.0}
        assert collector.validate(data) is True

    def test_validate_invalid_data(self, collector):
        """Test validation with invalid data."""
        data = {"price_usd": 0}
        assert collector.validate(data) is False


class TestEtherscanCollector:
    """Tests for Etherscan collector."""

    @pytest.fixture
    def collector(self):
        return EtherscanCollector()

    def test_parse_response_with_detailed_supply(self, collector):
        """Test parsing Etherscan supply response with breakdown."""
        raw_data = {
            "supply": {
                "result": {
                    "EthSupply": "120000000000000000000000000",  # Wei
                    "Eth2Staking": "32000000000000000000000000",
                    "BurntFees": "4000000000000000000000000",
                }
            },
            "eth2": {},
        }

        result = collector.parse(raw_data)

        assert result["total_supply_eth"] == pytest.approx(120_000_000, rel=0.01)
        assert result["eth2_staking_eth"] == pytest.approx(32_000_000, rel=0.01)
        assert result["total_burnt_eth"] == pytest.approx(4_000_000, rel=0.01)


class TestBeaconchainCollector:
    """Tests for Beaconchain collector."""

    @pytest.fixture
    def collector(self):
        return BeaconchainCollector()

    def test_parse_response(self, collector):
        """Test parsing Beaconchain response."""
        raw_data = {
            "network": {
                "data": {
                    "validatorscount": 900_000,
                    "totalvalidatorbalance": 32_000_000_000_000_000,  # Gwei
                }
            },
            "deposits": {},
            "withdrawals": {},
        }

        result = collector.parse(raw_data)

        assert result["active_validators"] == 900_000
        assert result["total_staked_eth"] == pytest.approx(32_000_000, rel=0.01)


class TestETFTrackerCollector:
    """Tests for ETF tracker collector."""

    @pytest.fixture
    def collector(self):
        return ETFTrackerCollector()

    @pytest.mark.asyncio
    async def test_fetch_returns_fallback(self, collector):
        """Test that fetch returns fallback data."""
        result = await collector.fetch()

        assert result["source"] == "estimated"
        assert "flows" in result

    def test_parse_response(self, collector):
        """Test parsing ETF flow data."""
        raw_data = {
            "source": "estimated",
            "markets_open": True,
            "flows": {
                "daily_flows_usd": [
                    {"date": "2024-01-01", "flow": 10_000_000},
                ],
                "weekly_total_usd": 50_000_000,
            },
        }

        result = collector.parse(raw_data)

        assert result["weekly_flow_usd"] == 50_000_000
        assert result["is_estimated"] is True

    @pytest.mark.asyncio
    async def test_manual_flow_input(self, collector):
        """Test setting manual flow data."""
        result = await collector.set_manual_flow(75_000_000)

        assert result["source"] == "manual"
        assert result["weekly_flow_usd"] == 75_000_000
        assert result["is_estimated"] is False


class TestDuneCollector:
    """Tests for Dune/Exchange flow collector."""

    @pytest.fixture
    def collector(self):
        return DuneCollector()

    def test_parse_fallback_data(self, collector):
        """Test parsing fallback exchange flow data."""
        raw_data = {
            "source": "estimated",
            "data": {
                "inflows_7d_eth": 150_000,
                "outflows_7d_eth": 180_000,
                "net_flow_7d_eth": -30_000,
                "exchange_reserves_eth": 15_000_000,
            },
        }

        result = collector.parse(raw_data)

        assert result["inflows_7d_eth"] == 150_000
        assert result["outflows_7d_eth"] == 180_000
        assert result["net_flow_7d_eth"] == -30_000
        assert result["is_estimated"] is True


class TestDerivativesCollector:
    """Tests for Derivatives collector."""

    @pytest.fixture
    def collector(self):
        return DerivativesCollector()

    def test_parse_fallback_data(self, collector):
        """Test parsing fallback derivatives data."""
        raw_data = {
            "source": "estimated",
            "open_interest": {
                "current_usd": 8_000_000_000,
                "change_7d_pct": 0.05,
            },
            "funding": {
                "average_rate": 0.01,
            },
            "liquidations": {
                "total_7d_usd": 150_000_000,
            },
        }

        result = collector.parse(raw_data)

        assert result["open_interest_usd"] == 8_000_000_000
        assert result["oi_change_7d_pct"] == 0.05
        assert result["funding_rate"] == 0.01
        assert result["liquidations_7d_usd"] == 150_000_000

    def test_calculate_stress_score_healthy(self, collector):
        """Test stress score calculation for healthy market."""
        data = {
            "oi_change_7d_pct": 0.05,
            "funding_rate": 0.01,
            "liquidations_7d_usd": 50_000_000,
        }

        score = collector.calculate_stress_score(data)
        assert score < 0.3  # Healthy

    def test_calculate_stress_score_stressed(self, collector):
        """Test stress score calculation for stressed market."""
        data = {
            "oi_change_7d_pct": 0.30,
            "funding_rate": 0.08,
            "liquidations_7d_usd": 600_000_000,
        }

        score = collector.calculate_stress_score(data)
        assert score > 0.6  # Stressed
