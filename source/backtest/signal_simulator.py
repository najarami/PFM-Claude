"""EFI signal simulator from historical price data."""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import pandas as pd
import numpy as np

from source.config import settings

logger = logging.getLogger(__name__)


class TradingAction(str, Enum):
    """Trading action based on EFI signal."""
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"


@dataclass
class SimulatedSignal:
    """A simulated EFI signal for a given date."""
    date: pd.Timestamp
    efi_value: int  # -5 to +5
    regime: str
    action: TradingAction
    components: dict  # Individual signal components S1-S5


class SignalSimulator:
    """
    Simulates historical EFI signals based on price momentum and volatility.

    This is a proxy simulation since true historical on-chain data would require
    extensive Dune/Etherscan queries. The simulation uses:
    - Price momentum as proxy for supply/demand signals
    - Volatility as proxy for leverage/stress signals
    """

    def __init__(self):
        self.config = settings.backtest
        self.buy_threshold = self.config.buy_threshold
        self.sell_threshold = self.config.sell_threshold

    def simulate_signals(self, price_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate simulated EFI signals for historical price data.

        Args:
            price_df: DataFrame with date and price columns

        Returns:
            DataFrame with EFI signals added
        """
        df = price_df.copy()
        df = df.sort_values("date").reset_index(drop=True)

        # Calculate momentum indicators
        df["return_7d"] = df["price"].pct_change(periods=7)
        df["return_14d"] = df["price"].pct_change(periods=14)
        df["return_30d"] = df["price"].pct_change(periods=30)

        # Calculate volatility
        df["volatility_7d"] = df["price"].pct_change().rolling(window=7).std()
        df["volatility_14d"] = df["price"].pct_change().rolling(window=14).std()

        # Calculate moving averages for trend
        df["sma_20"] = df["price"].rolling(window=20).mean()
        df["sma_50"] = df["price"].rolling(window=50).mean()
        df["trend"] = (df["sma_20"] > df["sma_50"]).astype(int)

        # Simulate individual signal components
        df["s1_value"] = df.apply(self._simulate_s1, axis=1)
        df["s2_value"] = df.apply(self._simulate_s2, axis=1)
        df["s3_value"] = df.apply(self._simulate_s3, axis=1)
        df["s4_value"] = df.apply(self._simulate_s4, axis=1)
        df["s5_value"] = df.apply(self._simulate_s5, axis=1)

        # Calculate composite EFI
        df["efi_value"] = (
            df["s1_value"] + df["s2_value"] + df["s3_value"] +
            df["s4_value"] + df["s5_value"]
        )

        # Classify regime and action
        df["regime"] = df["efi_value"].apply(self._classify_regime)
        df["action"] = df["efi_value"].apply(self._get_action)

        # Fill NaN values at start (due to rolling calculations)
        df = df.fillna(0)

        # Ensure EFI is integer and bounded
        df["efi_value"] = df["efi_value"].clip(-5, 5).astype(int)
        for col in ["s1_value", "s2_value", "s3_value", "s4_value", "s5_value"]:
            df[col] = df[col].clip(-1, 1).astype(int)

        logger.info(f"Simulated {len(df)} days of EFI signals")
        return df

    def _simulate_s1(self, row: pd.Series) -> int:
        """
        Simulate S1: Net Supply Change.

        Proxy: Price momentum suggests supply/demand imbalance.
        Strong uptrend = demand > supply = bullish.
        """
        ret_7d = row.get("return_7d", 0)
        if pd.isna(ret_7d):
            return 0

        if ret_7d >= self.config.strong_bullish_momentum:
            return 1
        elif ret_7d <= self.config.strong_bearish_momentum:
            return -1
        return 0

    def _simulate_s2(self, row: pd.Series) -> int:
        """
        Simulate S2: Staking Net Flow.

        Proxy: Longer-term trend suggests staking behavior.
        Sustained uptrend = stakers accumulating.
        """
        ret_30d = row.get("return_30d", 0)
        trend = row.get("trend", 0)

        if pd.isna(ret_30d):
            return 0

        if ret_30d > 0.10 and trend == 1:
            return 1
        elif ret_30d < -0.10 and trend == 0:
            return -1
        return 0

    def _simulate_s3(self, row: pd.Series) -> int:
        """
        Simulate S3: ETF Demand.

        Proxy: ETF flows correlate with institutional interest.
        Strong 14d momentum suggests institutional buying.
        Note: ETH ETFs launched in 2024, so pre-2024 is estimated.
        """
        ret_14d = row.get("return_14d", 0)

        if pd.isna(ret_14d):
            return 0

        if ret_14d >= 0.08:
            return 1
        elif ret_14d <= -0.08:
            return -1
        return 0

    def _simulate_s4(self, row: pd.Series) -> int:
        """
        Simulate S4: Exchange Flow.

        Proxy: Bullish momentum = outflows from exchanges.
        Moderate bullish = net outflow.
        """
        ret_7d = row.get("return_7d", 0)

        if pd.isna(ret_7d):
            return 0

        if ret_7d >= self.config.bullish_momentum:
            return 1
        elif ret_7d <= self.config.bearish_momentum:
            return -1
        return 0

    def _simulate_s5(self, row: pd.Series) -> int:
        """
        Simulate S5: Leverage & Stress.

        Proxy: High volatility = market stress.
        Low volatility in uptrend = healthy.
        """
        vol_7d = row.get("volatility_7d", 0)
        trend = row.get("trend", 0)

        if pd.isna(vol_7d):
            return 0

        # High volatility is bearish (stress)
        if vol_7d >= self.config.high_volatility:
            return -1
        # Low volatility in uptrend is bullish
        elif vol_7d < 0.03 and trend == 1:
            return 1
        return 0

    def _classify_regime(self, efi: int) -> str:
        """Classify EFI value into regime."""
        if efi >= 4:
            return "Explosive"
        elif efi >= 2:
            return "Constructive"
        elif efi >= -1:
            return "Neutral"
        elif efi >= -3:
            return "Fragile"
        else:
            return "Stress"

    def _get_action(self, efi: int) -> str:
        """Get trading action from EFI value."""
        if efi >= self.buy_threshold:
            return TradingAction.BUY.value
        elif efi <= self.sell_threshold:
            return TradingAction.SELL.value
        return TradingAction.HOLD.value

    def get_weekly_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Resample daily signals to weekly for trading decisions.

        Uses end-of-week EFI value for decision.
        """
        df = df.copy()
        df.set_index("date", inplace=True)

        # Resample to weekly, using last value of week
        weekly = df.resample("W").agg({
            "price": "last",
            "efi_value": "last",
            "regime": "last",
            "action": "last",
            "s1_value": "last",
            "s2_value": "last",
            "s3_value": "last",
            "s4_value": "last",
            "s5_value": "last",
        }).reset_index()

        weekly.rename(columns={"date": "week_end"}, inplace=True)

        # Drop any rows with NaN
        weekly = weekly.dropna()

        return weekly
