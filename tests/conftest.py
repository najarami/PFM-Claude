"""Pytest configuration and fixtures."""

import pytest
from datetime import datetime


@pytest.fixture
def sample_etherscan_data():
    """Sample Etherscan API response data."""
    return {
        "total_supply_eth": 120_000_000,
        "eth2_staking_eth": 32_000_000,
        "total_burnt_eth": 4_000_000,
    }


@pytest.fixture
def sample_beaconchain_data():
    """Sample Beaconchain API response data."""
    return {
        "active_validators": 900_000,
        "total_staked_eth": 32_000_000,
        "deposits_7d_eth": 50_000,
        "withdrawals_7d_eth": 40_000,
        "net_staking_flow_eth": 10_000,
    }


@pytest.fixture
def sample_etf_data():
    """Sample ETF flow data."""
    return {
        "source": "estimated",
        "markets_open": True,
        "weekly_flow_usd": 100_000_000,
        "avg_daily_flow_usd": 20_000_000,
        "daily_flows": [],
        "is_estimated": True,
    }


@pytest.fixture
def sample_exchange_data():
    """Sample exchange flow data."""
    return {
        "source": "estimated",
        "inflows_7d_eth": 150_000,
        "outflows_7d_eth": 200_000,
        "net_flow_7d_eth": -50_000,
        "exchange_reserves_eth": 15_000_000,
        "is_estimated": True,
    }


@pytest.fixture
def sample_derivatives_data():
    """Sample derivatives data."""
    return {
        "source": "estimated",
        "open_interest_usd": 8_000_000_000,
        "oi_change_7d_pct": 0.05,
        "funding_rate": 0.01,
        "liquidations_7d_usd": 100_000_000,
        "is_estimated": True,
    }


@pytest.fixture
def sample_s1_data():
    """Sample data for S1 signal calculation."""
    return {
        "emission_7d_eth": 11_900,  # ~1700 per day
        "burn_7d_eth": 14_000,      # ~2000 per day
        "net_supply_change_daily": -300,  # Deflationary
    }


@pytest.fixture
def sample_coingecko_data():
    """Sample CoinGecko API response data."""
    return {
        "price_usd": 3500.0,
        "market_cap_usd": 420_000_000_000,
        "volume_24h_usd": 15_000_000_000,
        "price_change_24h_pct": 2.5,
    }
