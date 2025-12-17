# Feature: ETH Flow Index (EFI)

## Feature Description
El ETH Flow Index (EFI) es un indicador semanal cuantitativo que mide el balance de oferta y demanda de Ethereum mediante 5 señales discretas (+1, 0, -1). El índice integra datos on-chain, flujos institucionales y métricas de derivados para anticipar movimientos de precio a un horizonte de 1 semana.

El sistema recolecta datos de múltiples fuentes gratuitas (CoinGecko, Etherscan, Beaconcha.in, Dune Analytics, fuentes de ETF), los procesa en señales normalizadas, calcula el EFI final (-5 a +5), y genera reportes visuales tanto en CLI como en un dashboard web futuro.

## User Story
As a crypto trader/analyst
I want to have a quantitative weekly index measuring ETH supply/demand balance
So that I can make data-driven decisions about ETH positions with a 1-week horizon

## Problem Statement
Los traders de ETH toman decisiones basadas en narrativas y sentimiento en lugar de flujos reales observables. No existe un indicador único que integre:
- Cambios en el supply del protocolo
- Absorción por staking
- Demanda institucional (ETFs)
- Oferta líquida en exchanges
- Riesgo por apalancamiento

Esto resulta en decisiones subóptimas y falta de un framework sistemático para evaluar el estado del mercado de ETH.

## Solution Statement
Construir un sistema Python modular que:
1. Recolecte datos de 5+ fuentes gratuitas via APIs
2. Normalice y agregue datos en ventanas semanales
3. Calcule 5 señales discretas (S₁ a S₅)
4. Genere un índice final EFI = S₁ + S₂ + S₃ + S₄ + S₅
5. Provea outputs en CLI, JSON/CSV, y dashboard web

## Relevant Files
Este es un proyecto nuevo. Los archivos de especificación existentes son:

- `eth_flow_index_efi_executive_summary.md` - Define los 5 componentes del EFI y su interpretación
- `indice_eth.md` - Descripción inicial del objetivo del índice

### New Files
```
source/
├── __init__.py
├── config.py                 # Configuración y API keys
├── main.py                   # Entry point CLI
├── collectors/
│   ├── __init__.py
│   ├── base.py              # Clase base para collectors
│   ├── coingecko.py         # Precio ETH, market data
│   ├── etherscan.py         # Supply, burn rate (S₁)
│   ├── beaconchain.py       # Staking flows (S₂)
│   ├── etf_tracker.py       # ETF flows (S₃)
│   ├── dune.py              # Exchange flows (S₄)
│   └── derivatives.py       # OI, funding, liquidations (S₅)
├── signals/
│   ├── __init__.py
│   ├── base.py              # Clase base para señales
│   ├── s1_net_supply.py     # Net Supply Change
│   ├── s2_staking.py        # Staking Net Flow
│   ├── s3_etf_demand.py     # ETF/DAT Demand
│   ├── s4_exchange.py       # Exchange Net Flow
│   └── s5_leverage.py       # Leverage & Stress
├── engine/
│   ├── __init__.py
│   ├── efi_calculator.py    # Cálculo del EFI final
│   └── interpreter.py       # Interpretación del régimen
├── storage/
│   ├── __init__.py
│   └── data_store.py        # Persistencia JSON/CSV
└── outputs/
    ├── __init__.py
    ├── cli_reporter.py      # Output CLI con tablas
    └── json_exporter.py     # Export JSON/CSV

tests/
├── __init__.py
├── test_collectors/
├── test_signals/
├── test_engine/
└── conftest.py

data/                        # Datos históricos cacheados
└── .gitkeep

app/                         # Dashboard web (fase futura)
├── server/
└── client/
```

## Implementation Plan

### Phase 1: Foundation
1. Inicializar proyecto Python con `uv`
2. Configurar estructura de directorios
3. Implementar sistema de configuración (API keys, thresholds)
4. Crear clases base para collectors y signals
5. Implementar data store para persistencia local

### Phase 2: Core Implementation
1. Implementar collectors para cada fuente de datos:
   - CoinGecko: precio ETH (referencia)
   - Etherscan: supply total, burn rate
   - Beaconcha.in: staking deposits/withdrawals
   - ETF sources: flujos de ETF (SoSoValue/Farside)
   - Dune/alternativas: exchange netflow
   - Coinglass/alternativas: OI, funding, liquidations
2. Implementar cálculo de cada señal S₁ a S₅
3. Implementar EFI calculator con lógica de agregación semanal
4. Implementar interpreter para clasificar regímenes

### Phase 3: Integration
1. Crear CLI runner con argumentos
2. Implementar reporter CLI con tablas formateadas
3. Implementar export JSON/CSV
4. Crear script de ejecución semanal
5. Documentar uso y mantenimiento

## Step by Step Tasks

### Step 1: Project Initialization
- Crear proyecto con `uv init`
- Configurar `pyproject.toml` con dependencias:
  - `httpx` - HTTP client async
  - `pydantic` - Validación de datos
  - `rich` - CLI tables y formatting
  - `python-dotenv` - Manejo de env vars
  - `pandas` - Manipulación de datos
- Crear estructura de directorios base
- Crear archivo `.env.example` con API keys necesarias

### Step 2: Configuration System
- Implementar `source/config.py`:
  - Cargar variables de entorno
  - Definir thresholds para cada señal
  - Validar configuración al iniciar
- Crear `.env` template con:
  - `COINGECKO_API_KEY`
  - `ETHERSCAN_API_KEY`
  - `BEACONCHAIN_API_KEY` (opcional)

### Step 3: Base Classes
- Implementar `source/collectors/base.py`:
  - `BaseCollector` con métodos `fetch()`, `parse()`, `validate()`
  - Manejo de rate limiting
  - Retry logic con backoff
- Implementar `source/signals/base.py`:
  - `BaseSignal` con método `calculate() -> int` (-1, 0, +1)
  - Logging de cálculos

### Step 4: Data Collectors - Precio y Supply
- Implementar `source/collectors/coingecko.py`:
  - Fetch precio actual ETH/USD
  - Fetch market cap, volumen 24h
  - Tests unitarios
- Implementar `source/collectors/etherscan.py`:
  - Fetch ETH total supply
  - Fetch ETH burned (últimos 7 días)
  - Calcular net issuance
  - Tests unitarios

### Step 5: Data Collectors - Staking
- Implementar `source/collectors/beaconchain.py`:
  - Fetch validator deposits (7d)
  - Fetch validator withdrawals (7d)
  - Calcular staking net flow
  - Tests unitarios
- Fallback: usar datos de Dune Analytics queries públicas

### Step 6: Data Collectors - ETF Flows
- Implementar `source/collectors/etf_tracker.py`:
  - Scrape SoSoValue o Farside para ETH ETF flows
  - Parsear datos semanales
  - Manejar casos sin datos (mercados cerrados)
  - Tests unitarios

### Step 7: Data Collectors - Exchange Flows
- Implementar `source/collectors/dune.py`:
  - Conectar a Dune API o usar queries públicas
  - Fetch exchange inflows/outflows (7d)
  - Alternativa: usar CryptoQuant free tier
  - Tests unitarios

### Step 8: Data Collectors - Derivatives
- Implementar `source/collectors/derivatives.py`:
  - Fetch Open Interest ETH
  - Fetch Funding Rate promedio
  - Fetch Liquidaciones (7d)
  - Fuentes: Coinglass, Coinalyze
  - Tests unitarios

### Step 9: Signal Calculators
- Implementar `source/signals/s1_net_supply.py`:
  - Input: emission, burn
  - Output: +1 (deflacionario), 0 (neutral), -1 (inflacionario)
  - Thresholds configurables
- Implementar `source/signals/s2_staking.py`:
  - Input: staking deposits, withdrawals
  - Output: +1 (net staking), 0, -1 (net unstaking)
- Implementar `source/signals/s3_etf_demand.py`:
  - Input: ETF net flows
  - Output: +1 (inflows), 0, -1 (outflows)
- Implementar `source/signals/s4_exchange.py`:
  - Input: exchange inflows, outflows
  - Output: +1 (net outflow), 0, -1 (net inflow)
- Implementar `source/signals/s5_leverage.py`:
  - Input: OI change, funding, liquidations
  - Output: +1 (healthy), 0, -1 (stressed)
- Tests unitarios para cada señal

### Step 10: EFI Engine
- Implementar `source/engine/efi_calculator.py`:
  - Orquestar collectors
  - Calcular todas las señales
  - Sumar EFI = S₁ + S₂ + S₃ + S₄ + S₅
  - Retornar resultado estructurado
- Implementar `source/engine/interpreter.py`:
  - Mapear EFI a régimen (Explosivo, Constructivo, Neutral, Frágil, Stress)
  - Generar recomendación operativa
- Tests de integración

### Step 11: Data Storage
- Implementar `source/storage/data_store.py`:
  - Guardar resultados históricos en JSON
  - Cargar histórico para comparación
  - Export a CSV
- Crear directorio `data/` para persistencia

### Step 12: CLI Output
- Implementar `source/outputs/cli_reporter.py`:
  - Tabla con 5 señales y sus valores
  - EFI final con color según régimen
  - Comparación vs semana anterior
  - Usar `rich` para formatting
- Implementar `source/outputs/json_exporter.py`:
  - Export JSON estructurado
  - Export CSV para análisis

### Step 13: Main Entry Point
- Implementar `source/main.py`:
  - Argumentos CLI: `--calculate`, `--history`, `--export`
  - Orquestar todo el flujo
  - Manejo de errores graceful
- Crear script `scripts/run_efi.sh` para ejecución

### Step 14: Documentation & Validation
- Crear `README.md` con:
  - Descripción del proyecto
  - Instrucciones de instalación
  - Configuración de API keys
  - Uso del CLI
  - Interpretación del EFI
- Ejecutar todos los tests
- Validar flujo end-to-end

## Testing Strategy

### Unit Tests
- Test cada collector individual con mocks de respuestas API
- Test cada signal calculator con datos conocidos
- Test EFI calculator con combinaciones de señales
- Test interpreter con cada rango de EFI

### Integration Tests
- Test flujo completo con APIs reales (rate limited)
- Test persistencia de datos
- Test export JSON/CSV

### Edge Cases
- APIs no disponibles (fallback graceful)
- Datos parciales (algunas fuentes fallan)
- Rate limiting alcanzado
- Datos fuera de rango esperado
- Primera ejecución sin histórico
- ETF markets cerrados (weekends)

## Acceptance Criteria
- [ ] El sistema calcula el EFI correctamente con datos reales
- [ ] Cada señal S₁-S₅ produce valores discretos (-1, 0, +1)
- [ ] El CLI muestra tabla formateada con colores
- [ ] Los datos se persisten en JSON para histórico
- [ ] Export CSV funciona correctamente
- [ ] El sistema maneja errores de API gracefully
- [ ] Todos los tests pasan
- [ ] Documentación completa en README

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `cd /Users/nicolasjaramillo/Documents/Proyecto_nuevo && uv run pytest -v` - Run all tests
- `cd /Users/nicolasjaramillo/Documents/Proyecto_nuevo && uv run python -m source.main --help` - Verify CLI works
- `cd /Users/nicolasjaramillo/Documents/Proyecto_nuevo && uv run python -m source.main --calculate` - Run full EFI calculation
- `cd /Users/nicolasjaramillo/Documents/Proyecto_nuevo && uv run python -m source.main --export json` - Test JSON export
- `cd /Users/nicolasjaramillo/Documents/Proyecto_nuevo && uv run python -m source.main --history` - Test historical view

## Notes

### API Rate Limits
- **CoinGecko Free**: 10-30 calls/min
- **Etherscan Free**: 5 calls/sec
- **Beaconcha.in Free**: 10 calls/min
- **Dune Free**: 10 queries/day

Implementar caching agresivo y respetar rate limits.

### Fuentes Alternativas
Si alguna fuente falla, considerar:
- **ultrasound.money** para datos de burn
- **rated.network** para staking
- **DefiLlama** para TVL como proxy

### Thresholds Iniciales (ajustables)
```python
THRESHOLDS = {
    "s1_net_supply": {
        "bullish": -1000,    # ETH/día (deflacionario)
        "bearish": 1000      # ETH/día (inflacionario)
    },
    "s2_staking": {
        "bullish": 10000,    # ETH net staked/semana
        "bearish": -10000
    },
    "s3_etf": {
        "bullish": 50_000_000,   # $50M inflows/semana
        "bearish": -50_000_000
    },
    "s4_exchange": {
        "bullish": -50000,   # ETH net outflow (negativo = bullish)
        "bearish": 50000
    },
    "s5_leverage": {
        "stress_oi_change": 0.20,    # 20% OI increase = stress
        "stress_funding": 0.05       # 5% funding = stressed
    }
}
```

### Fase 2: Dashboard Web
Una vez validado el core, implementar dashboard con:
- FastAPI backend
- React/Next.js frontend
- Gráficos históricos
- Alertas automáticas
