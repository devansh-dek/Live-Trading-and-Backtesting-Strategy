# Quantitative Multi-Timeframe Trading System

A Python research and execution platform for systematic crypto trading on **BTCUSDT**. Combines multi-timeframe signal generation, walk-forward out-of-sample validation, performance analytics, and Binance Testnet paper trading in a single modular codebase.

**Author:** Devansh Khandelwal

---

## Highlights

- **Multi-timeframe strategy** — 15m entries confirmed by a true 1h SMA trend filter (proper OHLCV resampling)
- **Unified signal engine** — identical logic in backtest and live; no code-path drift
- **Walk-forward validation** — rolling 6-month train / 1-month test windows over 18 months of data
- **Full analytics** — Sharpe, Sortino, Calmar, profit factor, drawdown, buy-and-hold benchmark
- **Production patterns** — typed config, SQLite audit log, pytest + GitHub Actions CI, HTML reports

---

## Strategy Overview

| Layer | Timeframe | Rule |
|-------|-----------|------|
| Trend filter | 1h (resampled) | Long bias when SMA(20) > SMA(60); short bias when SMA(20) < SMA(60) |
| Entry trigger | 15m | Long if 1h UP + RSI(14) rises ≥ 2 pts; short if 1h DOWN + RSI falls ≥ 2 pts |
| Exit | 15m | Close long below SMA(20); close short above SMA(20) |
| Risk | — | ATR(14) SL at 1.5×, TP at 2.5×; 1% equity risk per trade; 3% daily loss limit |

Full methodology: [docs/METHODOLOGY.md](docs/METHODOLOGY.md)

---

## Backtest Summary

**Dataset:** 52,512 bars · BTCUSDT 15m · Dec 2024 – Jun 2026  
**Capital:** $100,000 · Commission: 0.1%

| Metric | Strategy | Buy & Hold |
|--------|----------|------------|
| Total Return | −41.7% | −36.9% |
| Max Drawdown | 41.9% | — |
| Sharpe Ratio | −2.53 | — |
| Sortino Ratio | −0.55 | — |
| Trades | 275 | — |
| Win Rate | 25.5% | — |
| Profit Factor | 0.55 | — |

Walk-forward OOS (12 windows): strategy underperforms benchmark consistently — see [docs/RESULTS.md](docs/RESULTS.md).

> The system is designed to evaluate edge rigorously. Negative alpha in this period is a valid research outcome, not a failure of the infrastructure.

---

## Getting Started

### Prerequisites

- Python 3.10+
- pip / venv

### Install

```bash
git clone <repo-url>
cd Live-Trading-and-Backtesting-Strategy
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run

```bash
# Verify environment
python scripts/verify_setup.py

# Full backtest + HTML report
python run_backtest.py --report

# Walk-forward out-of-sample analysis
python run_walkforward.py

# Unit tests
pytest tests/ -v
```

### Paper Trading (Binance Testnet)

```bash
cp .env.example .env
# Add keys from https://testnet.binance.vision/

python scripts/test_connection.py
python scripts/run_live_once.py    # smoke test (1 iteration)
python run_live.py                 # continuous loop
```

---

## Repository Layout

```
├── config/config.py         Typed strategy, backtest, and walk-forward settings
├── src/
│   ├── quant/               Indicators, signal engine, risk manager
│   ├── data/                Binance data fetch and normalization
│   ├── backtesting/         Engine, metrics, walk-forward, HTML reports
│   ├── strategy/            backtesting.py strategy adapter
│   ├── trading/             Exchange wrapper, executor, live runner
│   └── storage/             SQLite signal and trade journal
├── scripts/                 Data fetch, connection test, utilities
├── tests/                   pytest unit tests
├── docs/                    Methodology and results write-ups
├── reports/                 Generated HTML backtest reports
└── data/                    Historical OHLCV and runtime artifacts
```

Design details: [ARCHITECTURE.md](ARCHITECTURE.md)

---

## Makefile

| Command | Description |
|---------|-------------|
| `make install` | Install package with dev dependencies |
| `make backtest` | Run full-period backtest |
| `make walkforward` | Run walk-forward OOS analysis |
| `make test` | pytest with coverage |
| `make fetch-data` | Download latest 18 months of 15m klines |
| `make live` | Start Testnet paper trading |

---

## Tech Stack

Python · pandas · numpy · backtesting.py · python-binance · matplotlib · pytest · GitHub Actions

---

## License

Educational and research use only. Not financial advice.
