# Architecture

System design for the multi-timeframe quantitative trading platform.

---

## Overview

The codebase separates **research** (backtesting, walk-forward, reporting) from **execution** (Testnet paper trading). Both paths consume the same signal engine, ensuring that live behavior matches simulated behavior.

```
┌─────────────────────────────────────────────────────────────┐
│                    MultiTimeframeSignalEngine               │
│         (indicators · entry/exit rules · ATR levels)        │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
     ┌─────────▼─────────┐          ┌─────────▼─────────┐
     │  MultiTFStrategy  │          │    LiveRunner     │
     │  (backtesting.py) │          │  (Testnet loop)   │
     └─────────┬─────────┘          └─────────┬─────────┘
               │                              │
     ┌─────────▼─────────┐          ┌─────────▼─────────┐
     │  metrics · report │          │ executor · journal  │
     │  walk-forward     │          │ risk manager        │
     └───────────────────┘          └───────────────────┘
```

---

## Design Principles

1. **Single signal source** — all entry/exit rules live in `src/quant/signals.py`
2. **Thin adapters** — strategy and live runner only translate data formats
3. **Reproducible research** — fixed config dataclasses, versioned data, trade CSV exports
4. **Auditability** — every live signal evaluation is persisted to SQLite

---

## Module Map

| Path | Responsibility |
|------|----------------|
| `src/quant/indicators.py` | Vectorized SMA, RSI, ATR |
| `src/quant/signals.py` | Multi-TF signal engine and context objects |
| `src/quant/risk.py` | Fixed-fractional sizing, daily loss circuit breaker |
| `src/data/pipeline.py` | Binance kline fetch, OHLCV normalization, resampling |
| `src/backtesting/backtest.py` | Backtest orchestration and trade export |
| `src/backtesting/metrics.py` | Sharpe, Sortino, Calmar, profit factor, drawdown |
| `src/backtesting/walk_forward.py` | Rolling out-of-sample window generator |
| `src/backtesting/report.py` | Equity curve and drawdown chart → HTML |
| `src/strategy/multi_tf.py` | Precomputed indicators for O(n) backtests |
| `src/trading/exchange.py` | Binance Testnet REST wrapper |
| `src/trading/executor.py` | Risk-based market order execution |
| `src/trading/live_runner.py` | Polling loop with journal integration |
| `src/storage/journal.py` | SQLite persistence for signals and fills |
| `config/config.py` | Frozen dataclass configuration |

---

## Multi-Timeframe Alignment

The 1h trend filter uses **proper temporal resampling**, not a bar-count approximation:

1. 15m OHLCV → resample to 1h (`open=first`, `high=max`, `low=min`, `close=last`)
2. Compute SMA(20) and SMA(60) on 1h closes
3. Label each 1h bar UP / DOWN / NEUTRAL
4. Forward-fill the label onto each 15m bar

This avoids look-ahead bias and misaligned confirmation bars.

---

## Backtest Performance

Indicators are precomputed once in `MultiTFStrategy.init()` and registered via `backtesting.py`'s `self.I()`. On 50k+ bars this reduces runtime from O(n²) to O(n).

---

## Walk-Forward Protocol

| Parameter | Value |
|-----------|-------|
| Train window | 6 months |
| Test window | 1 month (out-of-sample) |
| Step size | 1 month |
| Parameters | Fixed across windows (v1) |

Each test window produces independent return and trade-count metrics. Aggregate OOS metrics are computed across all windows.

---

## Live Execution Flow

1. Poll 15m klines every 60 seconds
2. Evaluate exit rules if in position; else evaluate entry rules
3. Log every evaluation (including HOLD) to SQLite
4. Submit market orders on Binance Testnet when signaled
5. Halt new entries if daily PnL breaches −3% of equity

Stop-loss and take-profit levels are computed and logged; exits are currently signal-driven rather than exchange OCO orders.

---

## Configuration

All tunables are defined as frozen dataclasses in `config/config.py`:

- `StrategyConfig` — indicator periods, ATR multipliers, risk limits
- `BacktestConfig` — initial capital, commission, slippage
- `WalkForwardConfig` — train/test window sizes

---

## Testing and CI

```
tests/test_indicators.py   Indicator correctness
tests/test_signals.py      Signal engine edge cases
tests/test_risk.py           Position sizing and loss limits
tests/test_metrics.py        Performance metric calculations
```

GitHub Actions (`.github/workflows/ci.yml`) runs ruff lint and pytest on every push to `main`.

---

## Extension Points

| Feature | How to add |
|---------|------------|
| New indicator | `src/quant/indicators.py` → wire into signal engine |
| New symbol | `StrategyConfig.symbol` + data fetch script |
| Parameter search | `backtesting.py` `.optimize()` with OOS guardrails |
| WebSocket feed | Replace polling in `LiveRunner` |
| Regime filter | Additional column in signal engine before entry |

---

## Known Limitations

1. Current parameters show negative OOS alpha in the evaluated period
2. Live SL/TP are informational; exits follow signal rules
3. Single-asset (BTCUSDT) scope
4. Polling-based live loop (60s), not event-driven
5. Flat commission model; slippage not yet modeled in backtest

These are documented scope boundaries for v1.
