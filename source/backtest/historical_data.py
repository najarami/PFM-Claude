"""Historical ETH price data fetcher."""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import httpx
import pandas as pd
import numpy as np

from source.config import settings

logger = logging.getLogger(__name__)


class HistoricalDataFetcher:
    """
    Fetches historical ETH price data from CoinGecko.

    Caches results to avoid repeated API calls.
    Falls back to synthetic data if API is unavailable.
    """

    def __init__(self):
        self.base_url = settings.api.coingecko_base_url
        self.cache_file = Path(settings.backtest.price_cache_file)
        self.cache_expiry_days = settings.backtest.cache_expiry_days

    async def fetch_eth_prices(
        self,
        start_date: str,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Fetch historical ETH prices.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (defaults to today)

        Returns:
            DataFrame with columns: date, price, volume, market_cap
        """
        end_date = end_date or datetime.now().strftime("%Y-%m-%d")

        # Check cache first
        cached_data = self._load_cache(start_date, end_date)
        if cached_data is not None:
            logger.info("Using cached price data")
            return cached_data

        logger.info(f"Fetching ETH prices from {start_date} to {end_date}")

        try:
            # Convert dates to timestamps
            start_ts = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
            end_ts = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())

            # Fetch from CoinGecko
            url = f"{self.base_url}/coins/ethereum/market_chart/range"
            params = {
                "vs_currency": "usd",
                "from": start_ts,
                "to": end_ts,
            }

            # Add API key if available
            headers = {}
            if settings.api.coingecko_api_key:
                headers["x-cg-demo-api-key"] = settings.api.coingecko_api_key

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url, params=params, headers=headers, timeout=30.0
                )
                response.raise_for_status()
                data = response.json()

            # Process response
            df = self._process_coingecko_response(data)

            # Cache the data
            self._save_cache(df, start_date, end_date)

            return df

        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            logger.warning(f"CoinGecko API error: {e}")
            logger.info("Falling back to synthetic price data for demonstration")
            return self._generate_synthetic_data(start_date, end_date)

    def _process_coingecko_response(self, data: dict) -> pd.DataFrame:
        """Process CoinGecko API response into DataFrame."""
        prices = data.get("prices", [])
        volumes = data.get("total_volumes", [])
        market_caps = data.get("market_caps", [])

        # Create DataFrame from prices
        df = pd.DataFrame(prices, columns=["timestamp", "price"])
        df["date"] = pd.to_datetime(df["timestamp"], unit="ms").dt.date
        df["date"] = pd.to_datetime(df["date"])

        # Add volume and market cap
        if volumes:
            vol_df = pd.DataFrame(volumes, columns=["timestamp", "volume"])
            df["volume"] = vol_df["volume"]

        if market_caps:
            cap_df = pd.DataFrame(market_caps, columns=["timestamp", "market_cap"])
            df["market_cap"] = cap_df["market_cap"]

        # Aggregate to daily (CoinGecko returns hourly for long ranges)
        df = df.groupby("date").agg({
            "price": "last",
            "volume": "sum" if "volume" in df.columns else "first",
            "market_cap": "last" if "market_cap" in df.columns else "first",
        }).reset_index()

        df = df.sort_values("date").reset_index(drop=True)

        logger.info(f"Processed {len(df)} days of price data")
        return df

    def _load_cache(
        self,
        start_date: str,
        end_date: str,
    ) -> Optional[pd.DataFrame]:
        """Load cached price data if valid."""
        if not self.cache_file.exists():
            return None

        try:
            with open(self.cache_file, "r") as f:
                cache = json.load(f)

            # Check if cache is expired
            cache_time = datetime.fromisoformat(cache.get("cached_at", "2000-01-01"))
            if datetime.now() - cache_time > timedelta(days=self.cache_expiry_days):
                logger.info("Cache expired")
                return None

            # Check if requested range is covered
            cached_start = cache.get("start_date")
            cached_end = cache.get("end_date")

            if cached_start and cached_end:
                if cached_start <= start_date and cached_end >= end_date:
                    df = pd.DataFrame(cache["data"])
                    df["date"] = pd.to_datetime(df["date"])

                    # Filter to requested range
                    mask = (df["date"] >= start_date) & (df["date"] <= end_date)
                    return df[mask].reset_index(drop=True)

            return None

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Cache load failed: {e}")
            return None

    def _save_cache(
        self,
        df: pd.DataFrame,
        start_date: str,
        end_date: str,
    ) -> None:
        """Save price data to cache."""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)

        # Convert DataFrame to serializable format
        cache_data = df.copy()
        cache_data["date"] = cache_data["date"].dt.strftime("%Y-%m-%d")

        cache = {
            "cached_at": datetime.now().isoformat(),
            "start_date": start_date,
            "end_date": end_date,
            "data": cache_data.to_dict(orient="records"),
        }

        with open(self.cache_file, "w") as f:
            json.dump(cache, f, indent=2)

        logger.info(f"Cached price data to {self.cache_file}")

    def _generate_synthetic_data(
        self,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """
        Generate synthetic ETH price data for demonstration.

        Creates realistic-looking price data based on historical ETH patterns:
        - Bull/bear cycles
        - Volatility clusters
        - General upward trend over long periods

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            DataFrame with synthetic price data
        """
        logger.info("Generating synthetic price data for demonstration")

        # Generate date range
        dates = pd.date_range(start=start_date, end=end_date, freq="D")
        n_days = len(dates)

        # Seed for reproducibility
        np.random.seed(42)

        # Historical ETH reference points (approximate)
        # 2020-01-01: ~$130, 2021-01-01: ~$730, 2021-11-10: ~$4800 (ATH)
        # 2022-06-01: ~$1800, 2023-01-01: ~$1200, 2024-01-01: ~$2300

        start_dt = datetime.strptime(start_date, "%Y-%m-%d")

        # Determine starting price based on date
        if start_dt.year <= 2020:
            base_price = 130 + (start_dt.month - 1) * 20
        elif start_dt.year == 2021:
            base_price = 730 + (start_dt.month - 1) * 340
        elif start_dt.year == 2022:
            base_price = 3000 - (start_dt.month - 1) * 150
        elif start_dt.year == 2023:
            base_price = 1200 + (start_dt.month - 1) * 100
        else:
            base_price = 2300 + (start_dt.month - 1) * 50

        # Generate price series with realistic characteristics
        # Daily returns with mean reversion and volatility clustering
        volatility = 0.03  # Base daily volatility ~3%
        mean_return = 0.0002  # Slight upward drift

        returns = np.zeros(n_days)
        vol = np.zeros(n_days)
        vol[0] = volatility

        for i in range(1, n_days):
            # GARCH-like volatility clustering
            vol[i] = 0.94 * vol[i-1] + 0.06 * abs(returns[i-1]) + 0.001

            # Add some regime changes (bull/bear)
            regime = np.sin(i / 90) * 0.001  # ~3 month cycles

            returns[i] = mean_return + regime + vol[i] * np.random.randn()

        # Convert returns to prices
        prices = base_price * np.cumprod(1 + returns)

        # Ensure prices don't go negative and stay reasonable
        prices = np.clip(prices, 50, 10000)

        # Generate volume (correlated with volatility)
        base_volume = 5e9
        volumes = base_volume * (1 + np.abs(returns) * 10) * np.random.uniform(0.8, 1.2, n_days)

        # Generate market cap (price * circulating supply ~120M)
        market_caps = prices * 120_000_000

        df = pd.DataFrame({
            "date": dates,
            "price": prices,
            "volume": volumes,
            "market_cap": market_caps,
        })

        logger.info(f"Generated {len(df)} days of synthetic price data")
        logger.warning("NOTE: Using synthetic data. For accurate backtesting, configure COINGECKO_API_KEY")

        return df

    def get_weekly_prices(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Resample daily prices to weekly.

        Args:
            df: Daily price DataFrame

        Returns:
            Weekly price DataFrame with OHLC and volume
        """
        df = df.copy()
        df.set_index("date", inplace=True)

        weekly = df.resample("W").agg({
            "price": ["first", "max", "min", "last"],
            "volume": "sum",
        })

        # Flatten column names
        weekly.columns = ["open", "high", "low", "close", "volume"]
        weekly = weekly.reset_index()
        weekly.rename(columns={"date": "week_end"}, inplace=True)

        # Calculate weekly return
        weekly["weekly_return"] = weekly["close"].pct_change()

        return weekly
