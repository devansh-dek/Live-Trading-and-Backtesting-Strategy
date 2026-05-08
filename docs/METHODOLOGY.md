# Methodology

Research methodology for the multi-timeframe momentum strategy.

---

## Hypothesis

Short-term RSI momentum on the 15-minute timeframe, when aligned with the higher-timeframe trend, can identify directional entries with favorable risk/reward using ATR-based stops.

**Null expectation:** In trending or mean-reverting regimes without a clear edge, the strategy should not outperform buy-and-hold after costs.

---

## Data

| Field | Value |
|-------|-------|
| Source | Binance public REST API (`/api/v3/klines`) |
| Symbol | BTCUSDT |
| Interval | 15 minutes |
| Period | Dec 2024 – Jun 2026 (~18 months) |
| Bars | 52,512 |
| Storage | `data/historical_data.csv` |

No survivorship bias (single liquid pair). Data is fetched programmatically via `scripts/fetch_data.py`.

---

## Signal Construction

### Higher timeframe (1h)

Resample 15m bars to 1h OHLCV. Compute SMA(20) and SMA(60) on 1h close:

- **UP** — SMA(20) > SMA(60)
- **DOWN** — SMA(20) < SMA(60)
- **NEUTRAL** — equal (rare)

Forward-fill the 1h label to each underlying 15m bar.

### Lower timeframe (15m)

Compute RSI(14), SMA(20), SMA(60), ATR(14) on 15m bars.

**Entry (flat only):**

| Direction | Conditions |
|-----------|------------|
| Long | 1h UP AND RSI change ≥ +2 |
| Short | 1h DOWN AND RSI change ≤ −2 |

**Exit (in position):**

| Position | Condition |
|----------|-----------|
| Long | Close < SMA(20) |
| Short | Close > SMA(20) |

### Risk

- Stop loss: entry ± 1.5 × ATR(14)
- Take profit: entry ± 2.5 × ATR(14)
- Position size: 1% of equity at risk per trade (fixed fractional)
- Daily circuit breaker: no new entries after −3% daily PnL

---

## Backtesting Setup

| Parameter | Value |
|-----------|-------|
| Framework | [backtesting.py](https://kernc.github.io/backtesting.py/) |
| Initial capital | $100,000 |
| Commission | 0.1% per side |
| Order type | Market on close |
| Benchmark | Buy-and-hold BTC |

---

## Walk-Forward Validation

To reduce overfitting risk, out-of-sample testing uses rolling windows:

```
|---- train (6mo) ----|-- test (1mo) --|
                      |---- train ------|-- test --|
                                         ...
```

- Parameters are **fixed** across all windows (no in-sample optimization in v1)
- Each test month is strictly out-of-sample relative to its preceding train window
- Aggregate OOS metrics combine all test windows

This protocol answers: *"Would this fixed rule set have worked on data it hadn't seen during design?"*

---

## Performance Metrics

| Metric | Definition |
|--------|------------|
| Total Return | (Final equity / Initial capital) − 1 |
| Max Drawdown | Largest peak-to-trough equity decline |
| Sharpe Ratio | Annualized excess return / volatility |
| Sortino Ratio | Annualized return / downside deviation |
| Calmar Ratio | Total return / max drawdown |
| Profit Factor | Gross profits / gross losses |
| Win Rate | Winning trades / total trades |
| Exposure | Fraction of bars with open position |

---

## Live Validation

Paper trading on **Binance Testnet** validates:

1. API authentication and order routing
2. Signal engine on live kline data
3. SQLite journal completeness (every signal logged)
4. Risk manager daily loss gate

Live results are not used to tune backtest parameters (prevents lookahead in research).

---

## Interpretation Guidelines

When presenting results:

1. Report **both** strategy and benchmark returns
2. Disclose walk-forward OOS degradation if present
3. Separate **infrastructure quality** from **strategy alpha**
4. Identify regime sensitivity (e.g., high trade count in volatile months)

Negative alpha with rigorous testing is a valid and informative outcome.
