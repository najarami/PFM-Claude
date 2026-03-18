# Finanzas Personales

Aplicación web para controlar ingresos y gastos mensuales a partir de cartolas bancarias.

## Inicio Rápido

### Requisitos
- Python 3.11+, `uv` (backend)
- Node.js 18+, `npm` (frontend)
- PostgreSQL (o Docker)

### 1. Base de datos con Docker

```bash
cd finanzas
docker-compose up db -d
```

### 2. Backend

```bash
cd backend
cp .env.example .env
uv sync
uv run alembic upgrade head        # Crea tablas + categorías iniciales
uv run uvicorn app.main:app --reload
# → http://localhost:8000
# → http://localhost:8000/docs  (Swagger UI)
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

## Bancos Soportados

| Banco | CSV | PDF |
|-------|-----|-----|
| Banco de Chile | ✅ | ✅ |
| BCI | ✅ | ✅ |
| Santander | ✅ | ✅ |
| MACH | ✅ | — |
| Tenpo | ✅ | — |
| Mercado Pago | ✅ | — |

## Funcionalidades

- **Carga de cartolas**: CSV y PDF, detección automática de banco
- **Deduplicación**: evita importar dos veces la misma transacción
- **Categorización automática**: por palabras clave, editable manualmente
- **Vista mensual**: ingresos y gastos con gráficos por categoría
- **Comparativo**: hasta 12 meses lado a lado
- **Presupuesto**: define límites por categoría y ve el % ejecutado

## API

Documentación interactiva: http://localhost:8000/docs

```
POST   /api/upload                         Sube cartola (CSV/PDF)
GET    /api/accounts                       Lista cuentas
POST   /api/accounts                       Crea cuenta
GET    /api/transactions                   Lista con filtros
PATCH  /api/transactions/{id}/category     Cambia categoría
GET    /api/summary/{year}/{month}         Resumen mensual
GET    /api/comparison?months=2024-01&...  Comparativo
GET    /api/budget?year=2024&month=1       Budget vs actual
PUT    /api/budget/{slug}                  Define presupuesto
```
