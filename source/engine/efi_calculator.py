"""EFI Calculator - orchestrates data collection and signal calculation."""

import asyncio
import logging
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel

from source.collectors import (
    CoinGeckoCollector,
    EtherscanCollector,
    BeaconchainCollector,
    ETFTrackerCollector,
    DuneCollector,
    DerivativesCollector,
)
from source.signals import (
    NetSupplySignal,
    StakingSignal,
    ETFDemandSignal,
    ExchangeFlowSignal,
    LeverageSignal,
)
from source.signals.base import SignalResult

logger = logging.getLogger(__name__)


class EFIResult(BaseModel):
    """Complete EFI calculation result."""

    timestamp: datetime
    efi_value: int  # -5 to +5
    signals: dict[str, SignalResult]
    raw_data: dict[str, Any]
    errors: list[str] = []
    is_partial: bool = False  # True if some data sources failed


class EFICalculator:
    """
    Main EFI calculation engine.

    Orchestrates:
    1. Data collection from all sources
    2. Signal calculation (S1-S5)
    3. EFI aggregation
    """

    def __init__(self):
        # Initialize collectors
        self.coingecko = CoinGeckoCollector()
        self.etherscan = EtherscanCollector()
        self.beaconchain = BeaconchainCollector()
        self.etf_tracker = ETFTrackerCollector()
        self.dune = DuneCollector()
        self.derivatives = DerivativesCollector()

        # Initialize signal calculators
        self.s1_calculator = NetSupplySignal()
        self.s2_calculator = StakingSignal()
        self.s3_calculator = ETFDemandSignal()
        self.s4_calculator = ExchangeFlowSignal()
        self.s5_calculator = LeverageSignal()

    async def calculate(self) -> EFIResult:
        """
        Perform full EFI calculation.

        Returns:
            EFIResult with all signals and final EFI value
        """
        errors: list[str] = []
        raw_data: dict[str, Any] = {}

        # Collect data from all sources concurrently
        logger.info("Collecting data from all sources...")

        collection_tasks = {
            "coingecko": self.coingecko.collect(),
            "etherscan": self.etherscan.collect(),
            "beaconchain": self.beaconchain.collect(),
            "etf": self.etf_tracker.collect(),
            "exchange": self.dune.collect(),
            "derivatives": self.derivatives.collect(),
        }

        results = await asyncio.gather(
            *collection_tasks.values(),
            return_exceptions=True,
        )

        # Process results
        for (name, _), result in zip(collection_tasks.items(), results):
            if isinstance(result, Exception):
                errors.append(f"{name}: {str(result)}")
                raw_data[name] = {}
            else:
                raw_data[name] = result

        # Calculate signals
        logger.info("Calculating signals...")
        signals = self._calculate_signals(raw_data)

        # Calculate final EFI
        efi_value = sum(s.value for s in signals.values())

        result = EFIResult(
            timestamp=datetime.now(),
            efi_value=efi_value,
            signals={name: signal for name, signal in signals.items()},
            raw_data=raw_data,
            errors=errors,
            is_partial=len(errors) > 0,
        )

        logger.info(f"EFI calculated: {efi_value}")
        return result

    def _calculate_signals(self, raw_data: dict[str, Any]) -> dict[str, SignalResult]:
        """Calculate all 5 signals from raw data."""
        signals = {}

        # S1: Net Supply
        s1_data = self._prepare_s1_data(raw_data)
        signals["S1"] = self.s1_calculator.calculate(s1_data)

        # S2: Staking
        s2_data = self._prepare_s2_data(raw_data)
        signals["S2"] = self.s2_calculator.calculate(s2_data)

        # S3: ETF Demand
        s3_data = raw_data.get("etf", {})
        signals["S3"] = self.s3_calculator.calculate(s3_data)

        # S4: Exchange Flow
        s4_data = raw_data.get("exchange", {})
        signals["S4"] = self.s4_calculator.calculate(s4_data)

        # S5: Leverage
        s5_data = raw_data.get("derivatives", {})
        signals["S5"] = self.s5_calculator.calculate(s5_data)

        return signals

    def _prepare_s1_data(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """Prepare data for S1 (Net Supply) calculation."""
        etherscan_data = raw_data.get("etherscan", {})

        # Estimate weekly emission and burn
        # Post-merge: ~1700 ETH/day issuance, variable burn
        total_burnt = etherscan_data.get("total_burnt_eth", 0)

        # Estimate daily values (simplified)
        # In production, would calculate actual 7-day change
        emission_daily = 1700  # Approximate post-merge issuance
        burn_daily = total_burnt / 365 if total_burnt > 0 else 2000  # Rough estimate

        return {
            "emission_7d_eth": emission_daily * 7,
            "burn_7d_eth": burn_daily * 7,
            "net_supply_change_daily": emission_daily - burn_daily,
        }

    def _prepare_s2_data(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """Prepare data for S2 (Staking) calculation."""
        beaconchain_data = raw_data.get("beaconchain", {})

        return {
            "deposits_7d_eth": beaconchain_data.get("deposits_7d_eth", 0),
            "withdrawals_7d_eth": beaconchain_data.get("withdrawals_7d_eth", 0),
            "net_staking_flow_eth": beaconchain_data.get("net_staking_flow_eth", 0),
        }

    async def close(self) -> None:
        """Close all collector connections."""
        await asyncio.gather(
            self.coingecko.close(),
            self.etherscan.close(),
            self.beaconchain.close(),
            self.dune.close(),
            self.derivatives.close(),
        )

    async def calculate_with_manual_data(
        self,
        s1_data: Optional[dict] = None,
        s2_data: Optional[dict] = None,
        s3_data: Optional[dict] = None,
        s4_data: Optional[dict] = None,
        s5_data: Optional[dict] = None,
    ) -> EFIResult:
        """
        Calculate EFI with manual/override data.

        Useful for backtesting or when automated collection fails.
        """
        signals = {}

        # Calculate each signal with provided or empty data
        signals["S1"] = self.s1_calculator.calculate(s1_data or {"net_supply_change_daily": 0})
        signals["S2"] = self.s2_calculator.calculate(s2_data or {"net_staking_flow_eth": 0})
        signals["S3"] = self.s3_calculator.calculate(s3_data or {"weekly_flow_usd": 0})
        signals["S4"] = self.s4_calculator.calculate(s4_data or {"net_flow_7d_eth": 0})
        signals["S5"] = self.s5_calculator.calculate(s5_data or {"oi_change_7d_pct": 0, "funding_rate": 0, "liquidations_7d_usd": 0})

        efi_value = sum(s.value for s in signals.values())

        return EFIResult(
            timestamp=datetime.now(),
            efi_value=efi_value,
            signals={name: signal for name, signal in signals.items()},
            raw_data={
                "s1": s1_data,
                "s2": s2_data,
                "s3": s3_data,
                "s4": s4_data,
                "s5": s5_data,
            },
            errors=[],
            is_partial=False,
        )
