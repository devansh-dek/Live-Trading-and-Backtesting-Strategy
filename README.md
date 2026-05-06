# Quantitative Multi-Timeframe Trading System

A production-oriented research and execution platform for systematic crypto trading. Implements a **multi-timeframe momentum strategy** on BTCUSDT with walk-forward out-of-sample validation, HTML performance reports, SQLite trade journaling, and Binance Testnet paper execution.

**Author:** Devansh Khandelwal

---

## What Makes This Defensible in Interviews

| Capability | Implementation |
|------------|----------------|
| **Multi-timeframe design** | 15m entry signals filtered by 1h SMA trend (true resampling, not bar-count hacks) |
| **Shared signal engine** | Same `MultiTimeframeSignalEngine` drives backtest and live — no logic drift |
| **Walk-forward OOS** | Rolling 6-month train / 1-month test windows across 18 months of data |
| **Risk layer** | ATR stops, fixed-fractional sizing, daily loss kill switch |
| **Benchmark** | Every backtest compares against buy-and-hold |
| **Audit trail** | SQLite journal logs every signal and fill |
| **Engineering** | pytest suite, GitHub Actions CI, typed config dataclasses |

---

## Strategy Logic

**1h trend filter (resampled from 15m):**
- UP: SMA(20) > SMA(60)
- DOWN: SMA(20) < SMA(60)

**15m entry (only when flat):**
- Long: 1h UP + RSI(14) rising ≥ 2 points
- Short: 1h DOWN + RSI(14) falling ≥ 2 points

**15m exit:**
- Long: close < SMA(20)
- Short: close > SMA(20)

**Risk:** ATR(14) stop at 1.5×, take-profit at 2.5×, 1% equity risk per trade.

---

## Results (18 months BTCUSDT 15m, Dec 2024 – Jun 2026)

| Metric | Strategy | Buy & Hold |
|--------|----------|------------|
| Total Return | -41.7% | -36.9% |
| Max Drawdown | 41.9% | — |
| Sharpe | -2.53 | — |
| Trades | 275 | — |
| Win Rate | 25.5% | — |
| Profit Factor | 0.55 | — |

> **Honest note:** Current parameters show negative out-of-sample alpha in this period. The platform is built to *detect* this rigorously — walk-forward confirms degradation. This is a research system, not a claimed edge. In interviews, lead with methodology, not returns.

Walk-forward: 12 OOS windows, aggregate 1,408 trades, consistent underperformance vs benchmark → strategy needs parameter refinement or regime filter.

---

## Quick Start

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Verify setup
python scripts/verify_setup.py

# Run backtest + HTML report
python run_backtest.py --report

# Walk-forward OOS analysis
python run_walkforward.py

# Run tests
pytest tests/ -v
```

### Live Paper Trading (Binance Testnet)

```bash
cp .env.example .env
# Add testnet keys from https://testnet.binance.vision/

python scripts/test_connection.py   # verify keys
python scripts/run_live_once.py     # single iteration smoke test
python run_live.py                  # continuous loop (Ctrl+C to stop)
```

---

## Project Structure

```
├── config/config.py          # StrategyConfig, BacktestConfig dataclasses
├── src/
│   ├── quant/                # Indicators, signals, risk (framework-agnostic)
│   ├── data/pipeline.py      # Binance data fetch + normalization
│   ├── backtesting/          # Engine, metrics, walk-forward, HTML reports
│   ├── strategy/multi_tf.py  # backtesting.py Strategy adapter
│   ├── trading/              # Exchange, executor, live runner
│   └── storage/journal.py    # SQLite signal + trade log
├── scripts/
│   ├── fetch_data.py         # Download 18mo of 15m klines
│   ├── test_connection.py    # Testnet auth check
│   └── run_live_once.py      # Single-iteration smoke test
├── tests/                    # pytest unit tests
├── reports/                  # Generated HTML backtest reports
└── data/
    ├── historical_data.csv   # 52k bars BTCUSDT 15m
    └── trading_journal.db    # Live signal/trade log (generated)
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for design details.

---

## Resume Bullet Examples

- Built a multi-timeframe quant research platform in Python with walk-forward OOS validation on 52k 15m bars, Sharpe/drawdown/profit-factor analytics, and buy-and-hold benchmarking.
- Designed a framework-agnostic signal engine shared between backtesting and live execution, with ATR-based risk sizing and SQLite audit logging.
- Integrated Binance Testnet paper trading with structured signal journaling; validated end-to-end pipeline via pytest + GitHub Actions CI.

---

## Makefile Commands

```bash
make install      # pip install -e ".[dev]"
make backtest     # full-period backtest
make walkforward  # OOS walk-forward
make test         # pytest + coverage
make fetch-data   # refresh historical data
make live         # start paper trading
```

---

## License

Educational / research use. Not financial advice.
