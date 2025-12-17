# Feature: EFI Backtest Engine

## Feature Description
A comprehensive backtesting system that evaluates the ETH Flow Index (EFI) against historical ETH prices from 2020 to present. The system determines optimal buy/hold/sell levels based on EFI signals, visualizes performance with interactive charts, and simulates portfolio returns starting with $100 initial investment compared against a buy-and-hold benchmark.

## User Story
As a quantitative analyst/investor
I want to backtest the EFI index against historical ETH price data
So that I can validate the index's predictive power and determine optimal trading signals for portfolio management

## Problem Statement
The EFI index currently calculates real-time signals but lacks historical validation. Without backtesting:
- Users cannot assess the index's historical accuracy
- Optimal buy/hold/sell thresholds are theoretical, not empirically validated
- There's no comparison against simple buy-and-hold strategy
- Users lack confidence in using EFI for actual investment decisions

## Solution Statement
Build a backtesting engine that:
1. Fetches historical ETH price data (2020-present) from CoinGecko
2. Simulates historical EFI values using available on-chain metrics or generates synthetic signals based on price momentum as proxy
3. Maps EFI regimes to trading actions (Buy/Hold/Sell)
4. Executes simulated trades and tracks portfolio value over time
5. Generates comparative visualizations (EFI signals + ETH price + portfolio value)
6. Calculates performance metrics vs buy-and-hold benchmark

## Relevant Files
Use these files to implement the feature:

- `source/config.py` - Add backtest configuration thresholds for signal-to-action mapping
- `source/collectors/coingecko.py` - Extend to fetch historical ETH price data
- `source/storage/data_store.py` - Reference for data persistence patterns
- `source/engine/efi_calculator.py` - Reference for `calculate_with_manual_data` method for manual signal injection
- `source/engine/interpreter.py` - Reference for regime classification logic
- `source/outputs/cli_reporter.py` - Reference for Rich output patterns
- `source/main.py` - Add `--backtest` CLI command

### New Files
- `source/backtest/__init__.py` - Package initialization
- `source/backtest/historical_data.py` - Historical ETH price fetcher
- `source/backtest/signal_simulator.py` - EFI signal simulation from historical data
- `source/backtest/backtester.py` - Core backtest engine with portfolio simulation
- `source/backtest/visualizer.py` - Chart generation with matplotlib
- `source/backtest/metrics.py` - Performance metrics calculator
- `tests/test_backtest/__init__.py` - Test package
- `tests/test_backtest/test_backtester.py` - Backtest engine tests

## Implementation Plan

### Phase 1: Foundation
Set up the backtest infrastructure and historical data fetching:
- Add matplotlib dependency for visualization
- Create backtest package structure
- Implement historical ETH price fetcher using CoinGecko API
- Add backtest configuration to `source/config.py`

### Phase 2: Core Implementation
Build the backtest engine and signal simulation:
- Create signal simulator that generates historical EFI values
- Implement portfolio simulator with buy/hold/sell logic
- Build metrics calculator for performance analysis
- Create visualization engine for charts

### Phase 3: Integration
Connect backtest to CLI and finalize outputs:
- Add `--backtest` command to CLI
- Integrate all components into unified backtest workflow
- Generate comprehensive backtest report with charts
- Export results to data directory

## Step by Step Tasks

### Step 1: Add matplotlib dependency
- Run `uv add matplotlib` to add visualization library
- Verify installation with import test

### Step 2: Create backtest package structure
- Create `source/backtest/__init__.py`
- Create empty module files for planned components

### Step 3: Add backtest configuration
- Add to `source/config.py`:
  - `BacktestConfig` class with signal-to-action thresholds
  - EFI regime to action mapping: Explosive/Constructive → Buy, Neutral → Hold, Fragile/Stress → Sell
  - Initial investment amount: $100
  - Backtest date range: 2020-01-01 to present

### Step 4: Implement historical data fetcher
- Create `source/backtest/historical_data.py`
- Implement `HistoricalDataFetcher` class:
  - Fetch daily ETH prices from CoinGecko (2020-present)
  - Cache results to avoid repeated API calls
  - Return DataFrame with date, price, volume columns

### Step 5: Implement signal simulator
- Create `source/backtest/signal_simulator.py`
- Implement `SignalSimulator` class:
  - Generate synthetic EFI signals based on price momentum and volatility as proxy
  - Use 7-day returns and volatility to estimate regime
  - Map to EFI values (-5 to +5)
  - Note: This is a simplified simulation; real historical on-chain data would require Dune/Etherscan historical queries

### Step 6: Implement portfolio backtester
- Create `source/backtest/backtester.py`
- Implement `Backtester` class:
  - Initialize with historical prices and EFI signals
  - Trading logic: Buy when EFI >= +2, Sell when EFI <= -2, Hold otherwise
  - Track portfolio value, positions, and transactions
  - Calculate returns at each timestamp
  - Implement buy-and-hold benchmark

### Step 7: Implement metrics calculator
- Create `source/backtest/metrics.py`
- Implement `BacktestMetrics` class:
  - Total return (%)
  - Annualized return
  - Max drawdown
  - Sharpe ratio
  - Win rate (profitable trades / total trades)
  - Compare vs buy-and-hold returns

### Step 8: Implement visualizer
- Create `source/backtest/visualizer.py`
- Implement `BacktestVisualizer` class:
  - Plot 1: ETH price with buy/sell markers
  - Plot 2: EFI value over time with regime bands
  - Plot 3: Portfolio value vs buy-and-hold
  - Save charts to `data/backtest_charts/`
  - Use matplotlib with clean, professional styling

### Step 9: Integrate CLI command
- Update `source/main.py`:
  - Add `--backtest` argument
  - Add `--start-date` and `--end-date` optional arguments
  - Add `--initial-investment` optional argument (default: 100)
  - Implement `run_backtest()` async function

### Step 10: Create backtest tests
- Create `tests/test_backtest/__init__.py`
- Create `tests/test_backtest/test_backtester.py`:
  - Test portfolio simulation with mock data
  - Test metrics calculations
  - Test signal-to-action mapping
  - Test edge cases (all buy, all sell, all hold)

### Step 11: Run validation commands
- Run pytest to ensure all tests pass
- Execute backtest with sample date range
- Verify chart generation

## Testing Strategy

### Unit Tests
- `test_historical_data.py`: Mock CoinGecko responses, test data parsing
- `test_signal_simulator.py`: Test signal generation logic, boundary conditions
- `test_backtester.py`: Test portfolio calculations with known inputs/outputs
- `test_metrics.py`: Test metric calculations (returns, Sharpe, drawdown)

### Integration Tests
- Test full backtest pipeline from data fetch to chart generation
- Test CLI integration with `--backtest` flag

### Edge Cases
- Empty price data handling
- Single day backtest
- All signals same direction (always buy/sell)
- Price data gaps
- Extreme price movements (>50% in a week)

## Acceptance Criteria
- [ ] Historical ETH price data fetched successfully for 2020-present
- [ ] EFI signals simulated for each week in the backtest period
- [ ] Portfolio simulation produces correct returns with $100 initial investment
- [ ] Buy/Hold/Sell signals mapped correctly based on EFI thresholds
- [ ] Three charts generated: Price+Signals, EFI Timeline, Portfolio Comparison
- [ ] Metrics report shows: Total Return, Max Drawdown, Sharpe Ratio, vs Buy-and-Hold
- [ ] CLI command `--backtest` executes full backtest workflow
- [ ] All tests pass with no regressions

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest -v` - Run all tests to validate no regressions
- `uv run pytest tests/test_backtest/ -v` - Run backtest-specific tests
- `uv run python -m source.main --backtest` - Execute full backtest (2020-present)
- `uv run python -m source.main --backtest --start-date 2023-01-01` - Test with custom date range
- `ls data/backtest_charts/` - Verify chart files generated
- `uv run python -m source.main --calculate` - Ensure existing functionality still works

## Notes
- **Data Limitation**: True historical EFI would require historical on-chain data from Dune Analytics and Etherscan. This implementation uses price-based proxy signals for demonstration. Future enhancement could integrate real historical data.
- **New Dependency**: `matplotlib` will be added via `uv add matplotlib`
- **Rate Limits**: CoinGecko free tier allows ~30 requests/minute. Historical data request should be batched and cached.
- **Signal Interpretation**: The mapping EFI → Action uses:
  - EFI >= +2 (Constructive/Explosive): BUY
  - -1 <= EFI <= +1 (Neutral): HOLD
  - EFI <= -2 (Fragile/Stress): SELL
- **Future Enhancements**:
  - Add position sizing based on signal strength
  - Implement stop-loss and take-profit levels
  - Add transaction costs/slippage simulation
  - Support multiple assets beyond ETH
