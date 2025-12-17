# ETH Flow Index (EFI)
## Executive Summary

---

## 1. Objetivo

El **ETH Flow Index (EFI)** es un **indicador semanal** diseñado para medir el **balance de oferta y demanda de Ethereum** y anticipar **movimientos de precio a un horizonte de 1 semana**.

El índice no se basa en narrativas, sino en **flujos reales y observables**:
- Quién compra ETH
- Quién vende ETH
- Cuánta oferta líquida entra o sale del mercado
- Qué tan sano o frágil es el bid (apalancamiento)

---

## 2. Idea Central

El precio de Ethereum se mueve cuando:

> **La demanda marginal (staking, ETF, compras spot)**  
> **supera a la oferta marginal (emisión neta, ventas naturales, estrés por leverage)**

El EFI traduce este balance en **una señal única, cuantificable y backtesteable**.

---

## 3. Qué mide el EFI

El índice combina **cinco bloques clave**, cada uno representando una dimensión distinta del flujo de ETH:

1. **Oferta monetaria neta del protocolo**  
2. **Absorción estructural vía staking**  
3. **Demanda financiera exógena (ETF / corporativa)**  
4. **Oferta líquida disponible para vender (exchanges)**  
5. **Calidad del bid y riesgo por apalancamiento**

Cada bloque se evalúa como:
- **+1** → buying power
- **0** → neutral
- **−1** → selling power

---

## 4. Cálculo del ETH Flow Index

El EFI se calcula como la suma simple de cinco señales discretas:

**EFI = S₁ + S₂ + S₃ + S₄ + S₅**

- **Rango:** −5 a +5  
- **Frecuencia de cálculo:** semanal  
- **Horizonte objetivo:** retorno de ETH a 1 semana

---

## 5. Componentes del EFI

### S₁ — Net Supply Change (ΔETH)

Mide si el supply de ETH **crece o se contrae neto**, integrando en una sola métrica:
- Emisión por rewards
- ETH quemado por fees

**Rol:** define el *viento monetario de fondo* del protocolo.

---

### S₂ — Staking Net Flow

Mide si ETH **entra o sale de staking**.

- ETH que entra a staking sale del float líquido
- Unstaking sostenido suele preceder presión vendedora

**Rol:** absorción estructural de oferta.

---

### S₃ — Demanda financiera exógena (ETF + DATs)

Captura compras **spot reales** provenientes de:
- ETFs de Ethereum
- Tesorerías corporativas / Digital Asset Treasuries

**Rol:** identificar al **comprador marginal price-insensitive**.

---

### S₄ — Exchange Net Flows

Mide si ETH **entra o sale de exchanges**.

- ETH entrando a exchanges ≈ ETH disponible para vender
- ETH saliendo de exchanges ≈ absorción / autocustodia

**Rol:** proxy directo de oferta líquida inmediata.

---

### S₅ — Leverage & Stress

Evalúa la **fragilidad del mercado** mediante:
- Open Interest en futuros
- Funding rates
- Liquidaciones

**Rol:** medir la calidad del bid (spot vs apalancado).

---

## 6. Interpretación del EFI

| EFI | Régimen | Lectura de Mercado |
|---|---|---|
| +4 / +5 | Explosivo | Bull leg / price discovery |
| +2 / +3 | Constructivo | Tendencia alcista sana |
| 0 / +1 | Neutral | Range / sin edge |
| −1 / −2 | Frágil | Riesgo de corrección |
| ≤ −3 | Stress | Downside elevado |

---

## 7. Uso Operativo (Horizonte 1 Semana)

- **Setup Long:** EFI ≥ +3 y sin señales de estrés por leverage
- **Señal de riesgo:** EFI ≤ −2 o deterioro abrupto del índice
- **No operar:** EFI entre −1 y +1

El EFI **no busca marcar el top exacto**, sino **anticipar cambios de régimen**.

---

## 8. Validación Histórica (Conceptual)

El marco del EFI es consistente con episodios históricos:
- EFI elevado antes de tramos alcistas sostenidos (ej. 2021, 2024)
- Colapso del índice antes de grandes drawdowns (ej. 2022)
- Deterioro del EFI previo a tops locales, antes de que el precio caiga

---

## 9. Datos Necesarios (Alto Nivel)

Para calcular el EFI se requieren **series diarias**, agregadas en ventanas de 7 días:

- Net supply change de ETH
- Flujos netos de staking
- Flujos de ETF / compras institucionales
- Exchange net flows
- Métricas de apalancamiento (OI, funding, liquidations)

Todos los datos se transforman en **señales semanales limpias**.

---

## 10. Por Qué es Útil

- Evita decisiones basadas en narrativa
- Integra onchain, financiero y microestructura
- Es replicable, auditable y backtesteable
- Se puede integrar directamente a frameworks de research y asset allocation

---

**Conclusión:**

El ETH Flow Index permite leer Ethereum como un **sistema de flujos**, no como una historia. Cuando el índice se alinea, el movimiento de precio suele seguir.

