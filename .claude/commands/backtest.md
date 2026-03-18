# Backtest EFI

> Ejecuta el backtest del ETH Flow Index y genera reportes completos con análisis de mejoras.

## Instrucciones

1. Ejecutar el backtest con datos reales de Yahoo Finance
2. Analizar los resultados con enfoque en forward return correlation
3. Generar reporte completo en `results/`
4. Proponer mejoras basadas en los hallazgos

## Ejecutar

```bash
# Limpiar cache para datos frescos (opcional)
rm -f data/eth_price_cache.json

# Ejecutar backtest
python3 -m source.main --backtest --start-date 2020-01-01
```

## Análisis Requerido

Después de ejecutar, analiza:

### 1. Forward Return Correlation
- ¿El EFI tiene poder predictivo? (correlaciones significativas p < 0.05)
- ¿Cuál es el mejor horizonte temporal?
- ¿Las correlaciones son positivas (como se espera)?

### 2. Análisis por Régimen
- ¿Qué valores de EFI generan mejores retornos?
- ¿Hay anomalías? (ej: zonas negativas con retornos positivos)
- ¿Los thresholds actuales son óptimos?

### 3. Métricas de Riesgo
- Max Drawdown: ¿Es aceptable?
- Sharpe Ratio: ¿Es > 1?
- Win Rate: ¿Puede mejorarse?

## Generar Reporte

Crear/actualizar el archivo `results/backtest_report_YYYY_YYYY.md` con:

1. **Resumen Ejecutivo**: Métricas clave en una tabla
2. **Forward Return Correlation**: Tabla con todos los horizontes
3. **Análisis por Régimen**: Retornos por valor EFI y por régimen
4. **Hallazgos Clave**: Fortalezas, debilidades, anomalías
5. **Recomendaciones de Mejora**: Prioridad alta/media/baja
6. **Próximos Pasos**: Tareas concretas

## Copiar Artefactos

```bash
# Copiar charts y JSON a results/
cp -r data/backtest_charts results/
cp data/backtest_results.json results/
```

## Mejoras a Considerar

Basado en análisis previos, evaluar:

### Prioridad Alta
- [ ] **Threshold de venta**: ¿-2 es óptimo o -3 sería mejor?
- [ ] **Señal contrarian**: ¿EFI extremo negativo indica rebote?
- [ ] **Walk-forward validation**: Separar train/test para evitar overfitting

### Prioridad Media
- [ ] **Position sizing dinámico**: Mayor tamaño en señales de alta confianza
- [ ] **Filtro de momentum**: No solo nivel de EFI, también dirección
- [ ] **Trailing stop loss**: Reducir max drawdown

### Prioridad Baja
- [ ] **Multi-timeframe**: EFI semanal + diario
- [ ] **Datos on-chain reales**: Integrar APIs de Etherscan, Dune, etc.

## Output Esperado

```
results/
├── backtest_report_2020_2025.md    # Reporte completo
├── backtest_results.json            # Datos crudos
└── backtest_charts/
    ├── price_with_signals.png       # Precio + señales
    ├── efi_timeline.png             # EFI en el tiempo
    ├── portfolio_comparison.png     # vs Buy & Hold
    ├── backtest_dashboard.png       # Dashboard completo
    ├── correlation_summary.png      # Correlaciones
    ├── forward_correlation_7d.png   # Scatter 7 días
    └── regime_returns.png           # Retornos por régimen
```

## Argumentos Opcionales

$ARGUMENTS

Si se proporciona un argumento, usarlo como fecha de inicio:
```bash
python3 -m source.main --backtest --start-date $ARGUMENTS
```
