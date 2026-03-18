# CLAUDE.md

## Project: ETH Flow Index (EFI)

Quantitative weekly index measuring ETH supply/demand balance via 5 signals (-1, 0, +1).

## Quick Commands

```bash
uv run pytest -v                          # Run tests
uv run python -m source.main --calculate  # Calculate EFI
uv run python -m source.main --history    # View history
uv run python -m source.main --export json # Export data
```

## Architecture

```
source/
├── collectors/   # API data fetchers (CoinGecko, Etherscan, etc.)
├── signals/      # S1-S5 calculators
├── engine/       # EFI calculator + interpreter
├── storage/      # JSON/CSV persistence
└── outputs/      # CLI reporter + exporters
```

## Signal Components

| Signal | Metric | Bullish |
|--------|--------|---------|
| S1 | Net Supply | Deflationary |
| S2 | Staking Flow | Net deposits |
| S3 | ETF Demand | Inflows |
| S4 | Exchange Flow | Net outflows |
| S5 | Leverage | Low stress |

## Regimes

- **+4 to +5**: Explosive (strong bullish)
- **+2 to +3**: Constructive (moderate bullish)
- **-1 to +1**: Neutral
- **-2 to -3**: Fragile (moderate bearish)
- **-4 to -5**: Stress (strong bearish)

## Key Files

- `source/config.py` - Thresholds and API config
- `source/engine/efi_calculator.py` - Main calculation logic
- `source/engine/interpreter.py` - Regime classification
- `specs/eth_flow_index.md` - Full specification
