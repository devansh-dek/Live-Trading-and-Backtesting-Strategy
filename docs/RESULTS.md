# Results

Backtest and walk-forward results for the multi-timeframe momentum strategy on BTCUSDT.

---

## Full-Period Backtest

**Period:** Dec 29, 2024 – Jun 29, 2026  
**Bars:** 52,512 (15m)  
**Capital:** $100,000

### Strategy vs Benchmark

| Metric | Strategy | Buy & Hold |
|--------|----------|------------|
| Total Return | −41.66% | −36.91% |
| Final Equity | $58,335 | $63,095 |
| Max Drawdown | 41.93% | — |
| Sharpe Ratio | −2.53 | — |
| Sortino Ratio | −0.55 | — |
| Calmar Ratio | −0.99 | — |
| Trades | 275 | — |
| Win Rate | 25.45% | — |
| Profit Factor | 0.55 | — |
| Avg Trade PnL | −$151.51 | — |
| Market Exposure | 1.84% | 100% |

### Observations

- Strategy loses less alpha than raw directionality might suggest, but still underperforms buy-and-hold
- Low win rate (25%) with profit factor below 1.0 indicates negative expectancy per trade
- Low exposure (1.84%) suggests the strategy is often flat — filters are restrictive but not selective enough
- BTC declined ~37% over the period; momentum-long signals in a bear market contributed to losses

---

## Walk-Forward Out-of-Sample

**Protocol:** 6-month train / 1-month test, 1-month step  
**Windows:** 12

| Window | Test Period | Return | Trades |
|--------|-------------|--------|--------|
| 1 | Jun – Jul 2025 | 0.00% | 0 |
| 2 | Jul – Aug 2025 | 0.00% | 0 |
| 3 | Aug – Sep 2025 | 0.00% | 0 |
| 4 | Sep – Oct 2025 | 0.00% | 0 |
| 5 | Oct – Nov 2025 | −15.77% | 48 |
| 6 | Nov – Dec 2025 | −15.12% | 56 |
| 7 | Dec 2025 – Jan 2026 | −12.55% | 68 |
| 8 | Jan – Feb 2026 | −35.87% | 243 |
| 9 | Feb – Mar 2026 | −33.65% | 209 |
| 10 | Mar – Apr 2026 | −29.62% | 220 |
| 11 | Apr – May 2026 | −26.58% | 190 |
| 12 | May – Jun 2026 | −41.22% | 374 |

### Aggregate OOS

| Metric | Value |
|--------|-------|
| Total Return | −41.22% |
| Max Drawdown | 42.62% |
| Sharpe | −0.12 |
| Trades | 1,408 |
| Win Rate | 21.38% |
| Profit Factor | 0.36 |

Early windows (1–4) generated zero trades — insufficient signal frequency in that regime. Later windows show increasing trade counts and deteriorating performance during high-volatility periods.

---

## Conclusions

1. **Fixed parameters do not produce positive OOS alpha** on BTCUSDT over this period
2. **Walk-forward confirms** full-sample results are not an artifact of a single lucky split
3. **Infrastructure behaves correctly** — 275 full-sample trades, consistent logging, benchmark comparison
4. **Next research steps:** regime filter (e.g., volatility gate), parameter sensitivity analysis, long-only mode in bear markets, wider stop targets

---

## Reproducing Results

```bash
source venv/bin/activate
python run_backtest.py --report
python run_walkforward.py
```

Trade log: `data/backtest_trades.csv`  
HTML report: `reports/backtest_report_*.html`
