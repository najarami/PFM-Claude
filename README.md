# ETH Flow Index (EFI)

A quantitative weekly index measuring ETH supply/demand balance through 5 discrete signals.

## Overview

The ETH Flow Index (EFI) integrates on-chain data, institutional flows, and derivatives metrics to anticipate ETH price movements over a 1-week horizon.

### Signal Components

| Signal | Name | Description |
|--------|------|-------------|
| S1 | Net Supply Change | Measures ETH emission vs burn (deflation is bullish) |
| S2 | Staking Net Flow | Net ETH flowing into/out of staking |
| S3 | ETF Demand | Institutional demand via ETH ETF flows |
| S4 | Exchange Flow | Net ETH movement to/from exchanges |
| S5 | Leverage & Stress | Market stress from derivatives metrics |

Each signal produces a value of **-1** (bearish), **0** (neutral), or **+1** (bullish).

### EFI Value & Regimes

EFI = S1 + S2 + S3 + S4 + S5 (range: -5 to +5)

| EFI Range | Regime | Description |
|-----------|--------|-------------|
| +4 to +5 | Explosive | Strong bullish alignment |
| +2 to +3 | Constructive | Moderately bullish |
| -1 to +1 | Neutral | Mixed signals |
| -2 to -3 | Fragile | Moderately bearish |
| -4 to -5 | Stress | Strong bearish alignment |

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Proyecto_nuevo
```

2. Install dependencies with uv:
```bash
uv sync
```

3. Configure API keys:
```bash
cp .env.example .env
# Edit .env with your API keys
```

## Usage

### Calculate Current EFI

```bash
uv run python -m source.main --calculate
```

### View Historical Data

```bash
uv run python -m source.main --history
```

### Export Results

```bash
# Export to JSON
uv run python -m source.main --export json

# Export to CSV
uv run python -m source.main --export csv
```

### CLI Options

```
--calculate     Calculate current EFI value
--history       Display historical EFI values
--export        Export results (json or csv)
--limit N       Limit for history display (default: 10)
--no-save       Don't save result to history
--verbose, -v   Enable verbose output
--quiet, -q     Only show EFI value
```

## Data Sources

| Source | Data | Rate Limit |
|--------|------|------------|
| CoinGecko | ETH price, market data | 10-30/min |
| Etherscan | Supply, burn rate | 5/sec |
| Beaconcha.in | Staking deposits/withdrawals | 10/min |
| SoSoValue/Farside | ETF flows | Manual/estimated |
| Dune Analytics | Exchange flows | 10 queries/day |
| Coinglass | OI, funding, liquidations | 20/min |

## Project Structure

```
source/
├── config.py              # Configuration and API keys
├── main.py                # CLI entry point
├── collectors/            # Data collectors for each source
│   ├── base.py           # Base collector class
│   ├── coingecko.py      # Price and market data
│   ├── etherscan.py      # Supply and burn data
│   ├── beaconchain.py    # Staking data
│   ├── etf_tracker.py    # ETF flow data
│   ├── dune.py           # Exchange flow data
│   └── derivatives.py    # Derivatives data
├── signals/               # Signal calculators
│   ├── base.py           # Base signal class
│   ├── s1_net_supply.py  # Net Supply Change
│   ├── s2_staking.py     # Staking Net Flow
│   ├── s3_etf_demand.py  # ETF Demand
│   ├── s4_exchange.py    # Exchange Flow
│   └── s5_leverage.py    # Leverage & Stress
├── engine/                # Core calculation engine
│   ├── efi_calculator.py # Main EFI calculation
│   └── interpreter.py    # Regime interpretation
├── storage/               # Data persistence
│   └── data_store.py     # JSON/CSV storage
└── outputs/               # Output formatters
    ├── cli_reporter.py   # CLI display with Rich
    └── json_exporter.py  # JSON/CSV export
```

## Running Tests

```bash
uv run pytest -v
```

## Configuration

Thresholds can be adjusted in `source/config.py`:

```python
THRESHOLDS = {
    "s1_net_supply": {
        "bullish": -1000,    # ETH/day (deflation threshold)
        "bearish": 1000      # ETH/day (inflation threshold)
    },
    "s2_staking": {
        "bullish": 10000,    # ETH net staked/week
        "bearish": -10000
    },
    "s3_etf": {
        "bullish": 50_000_000,   # $50M inflows/week
        "bearish": -50_000_000
    },
    "s4_exchange": {
        "bullish": -50000,   # ETH net outflow
        "bearish": 50000
    },
    "s5_leverage": {
        "stress_oi_change": 0.20,
        "stress_funding": 0.05
    }
}
```

## Interpretation Guide

### Explosive (+4 to +5)
All or most signals aligned bullish. Strong supply absorption. Consider full position with high conviction.

### Constructive (+2 to +3)
Mostly bullish signals. Favorable accumulation dynamics. Maintain or build position via DCA.

### Neutral (-1 to +1)
Mixed signals. No clear directional bias. Reduce position size and wait for clarity.

### Fragile (-2 to -3)
Mostly bearish signals. Distribution phase likely. Defensive positioning recommended.

### Stress (-4 to -5)
All or most signals aligned bearish. Risk-off environment. Maximum caution, preserve capital.

## License

MIT License
