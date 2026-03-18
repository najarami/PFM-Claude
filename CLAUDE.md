# CLAUDE.md — Personal Finance Manager (PFM)

## Stack
- **Backend**: FastAPI + SQLAlchemy async + PostgreSQL + Alembic
- **Frontend**: React 18 + TypeScript + TailwindCSS + Recharts + TanStack Query + Zustand
- **FX API**: api.frankfurter.app (free, no key required)

## Quick Commands

```bash
# Backend
cd finanzas/backend
uv run alembic upgrade head          # Run migrations
uv run uvicorn app.main:app --reload # Start API (port 8000)

# Frontend
cd finanzas/frontend
npm run dev                          # Start UI (port 5173)

# Docker (PostgreSQL)
cd finanzas
docker-compose up db -d
```

## Architecture

```
finanzas/
├── backend/app/
│   ├── models/        # SQLAlchemy ORM (Account, Transaction, Category, Budget, FxRate, UploadLog)
│   ├── routers/       # FastAPI endpoints (accounts, upload, transactions, summary, comparison, budget, fx)
│   ├── services/      # Business logic (upload, dedup, category, summary, budget, fx)
│   ├── parsers/       # Bank CSV/PDF parsers (6 Chilean + 6 US banks)
│   └── schemas/       # Pydantic request/response models
└── frontend/src/
    ├── pages/         # Dashboard, Transactions, MonthlyView, Comparison, BudgetSettings, Upload, Accounts
    ├── components/    # Charts, layout, UI (CurrencyToggle, ConversionBadge, BudgetGauge, etc.)
    ├── api/           # API client (summary, budget, transactions, accounts)
    └── store/         # Zustand (monthStore: year, month, currency, viewMode)
```

## Multi-Currency

Transactions store their native currency (CLP or USD).
Two view modes controlled by `viewMode` in `monthStore`:

- **native**: filters transactions by selected currency (original behavior)
- **converted**: fetches all transactions and converts each using the historical FX rate on the transaction date

FX rates are cached in the `fx_rates` table. Source: `api.frankfurter.app`.
Endpoint: `GET /api/fx/rate?from=USD&to=CLP&rate_date=2024-03-15`

## Migrations
- 0001: Initial schema + seed categories
- 0002: Add currency to budgets
- 0003: Add fx_rates table + fix dedup hash to include currency

## Supported Banks
**Chilean**: Banco de Chile, BCI, Santander, MACH, Tenpo, Mercado Pago
**US**: Bank of America, Chase, Wells Fargo, Schwab, Amex, Citi
