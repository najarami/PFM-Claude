# Prime
> Execute the following sections to understand the ETH Flow Index (EFI) codebase then summarize your understanding.

## Run
git ls-files

## Read
CLAUDE.md
README.md
specs/eth_flow_index.md

## Summary
After reading, provide:
1. Project purpose: ETH Flow Index quantitative indicator
2. The 5 signals (S1-S5) and what each measures
3. Key directories: source/collectors, source/signals, source/engine, source/outputs
4. Data flow: collectors → signals → EFI calculator → interpreter → CLI output
5. Available CLI commands: --calculate, --history, --export
6. How to run tests: `uv run pytest -v`
