"""Configuration management for ETH Flow Index."""

import os
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class APIConfig(BaseModel):
    """API keys and endpoints configuration."""

    coingecko_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("COINGECKO_API_KEY")
    )
    etherscan_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("ETHERSCAN_API_KEY")
    )
    beaconchain_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("BEACONCHAIN_API_KEY")
    )
    dune_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("DUNE_API_KEY")
    )

    # API endpoints
    coingecko_base_url: str = "https://api.coingecko.com/api/v3"
    etherscan_base_url: str = "https://api.etherscan.io/api"
    beaconchain_base_url: str = "https://beaconcha.in/api/v1"


class ThresholdsConfig(BaseModel):
    """Thresholds for signal calculations."""

    # S1: Net Supply Change (ETH/day)
    s1_bullish: float = -1000  # Deflacionario
    s1_bearish: float = 1000   # Inflacionario

    # S2: Staking Net Flow (ETH/week)
    s2_bullish: float = 10000   # Net staked
    s2_bearish: float = -10000  # Net unstaked

    # S3: ETF Demand (USD/week)
    s3_bullish: float = 50_000_000   # $50M inflows
    s3_bearish: float = -50_000_000  # $50M outflows

    # S4: Exchange Net Flow (ETH/week) - Negative = outflow = bullish
    s4_bullish: float = -50000  # Net outflow (bullish)
    s4_bearish: float = 50000   # Net inflow (bearish)

    # S5: Leverage & Stress
    s5_stress_oi_change: float = 0.20  # 20% OI increase
    s5_stress_funding: float = 0.05    # 5% funding rate


class BacktestConfig(BaseModel):
    """Configuration for backtesting."""

    # Default backtest period
    default_start_date: str = "2020-01-01"
    default_initial_investment: float = 100.0

    # EFI to action thresholds
    buy_threshold: int = 2       # EFI >= +2 -> BUY (Constructive/Explosive)
    sell_threshold: int = -2     # EFI <= -2 -> SELL (Fragile/Stress)
    # -1 <= EFI <= +1 -> HOLD (Neutral)

    # Signal simulation parameters (price-based proxy)
    momentum_window: int = 7     # Days for momentum calculation
    volatility_window: int = 14  # Days for volatility calculation

    # Momentum thresholds for signal generation
    strong_bullish_momentum: float = 0.15   # 15% weekly gain
    bullish_momentum: float = 0.05          # 5% weekly gain
    bearish_momentum: float = -0.05         # 5% weekly loss
    strong_bearish_momentum: float = -0.15  # 15% weekly loss

    # Volatility thresholds
    high_volatility: float = 0.10           # 10% weekly volatility = stress

    # Output paths
    charts_dir: str = "data/backtest_charts"
    results_file: str = "data/backtest_results.json"

    # Cache settings
    price_cache_file: str = "data/eth_price_cache.json"
    cache_expiry_days: int = 1  # Re-fetch prices daily


class Settings(BaseModel):
    """Main settings container."""

    api: APIConfig = Field(default_factory=APIConfig)
    thresholds: ThresholdsConfig = Field(default_factory=ThresholdsConfig)
    backtest: BacktestConfig = Field(default_factory=BacktestConfig)

    # Data storage paths
    data_dir: str = "data"
    history_file: str = "efi_history.json"

    # Rate limiting (requests per minute)
    coingecko_rpm: int = 10
    etherscan_rps: int = 5
    beaconchain_rpm: int = 10

    # Retry configuration
    max_retries: int = 3
    retry_backoff: float = 1.0  # seconds

    def validate_api_keys(self) -> dict[str, bool]:
        """Check which API keys are configured."""
        return {
            "coingecko": self.api.coingecko_api_key is not None,
            "etherscan": self.api.etherscan_api_key is not None,
            "beaconchain": self.api.beaconchain_api_key is not None,
            "dune": self.api.dune_api_key is not None,
        }


# Global settings instance
settings = Settings()
