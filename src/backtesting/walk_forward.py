"""Walk-forward analysis engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
from backtesting import Backtest

from config.config import BACKTEST, WALK_FORWARD, StrategyConfig
from src.backtesting.metrics import compute_metrics, format_metrics_table
from src.backtesting.backtest import prepare_backtest_data, get_strategy_class
from src.data.pipeline import normalize_ohlcv


@dataclass
class WalkForwardResult:
  windows: list[dict[str, Any]]
  aggregate_metrics: dict[str, Any]
  oos_equity: pd.Series


def generate_windows(
  df: pd.DataFrame,
  train_months: int = WALK_FORWARD.train_months,
  test_months: int = WALK_FORWARD.test_months,
) -> list[tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp, pd.Timestamp]]:
  """Return (train_start, train_end, test_start, test_end) tuples."""
  df = normalize_ohlcv(df)
  start = df.index[0]
  end = df.index[-1]
  windows = []
  cursor = start

  while True:
    train_end = cursor + pd.DateOffset(months=train_months)
    test_start = train_end
    test_end = test_start + pd.DateOffset(months=test_months)
    if test_end > end:
      break
    windows.append((cursor, train_end, test_start, test_end))
    cursor = cursor + pd.DateOffset(months=test_months)

  return windows


def run_walk_forward(
  df: pd.DataFrame,
  strategy_config: StrategyConfig | None = None,
) -> WalkForwardResult:
  df = normalize_ohlcv(df)
  windows_meta = generate_windows(df)
  StrategyClass = get_strategy_class(strategy_config)

  oos_segments: list[pd.Series] = []
  window_results: list[dict[str, Any]] = []

  for train_start, train_end, test_start, test_end in windows_meta:
    test_df = df.loc[test_start:test_end]
    if len(test_df) < 100:
      continue

    bt_df = prepare_backtest_data(test_df)
    bt = Backtest(
      bt_df,
      StrategyClass,
      cash=BACKTEST.initial_cash,
      commission=BACKTEST.commission,
      trade_on_close=BACKTEST.trade_on_close,
      exclusive_orders=True,
      finalize_trades=True,
    )
    stats = bt.run()
    trades = stats._trades
    equity = stats._equity_curve["Equity"]

    metrics = compute_metrics(equity, trades, BACKTEST.initial_cash)
    window_results.append({
      "train_start": train_start,
      "train_end": train_end,
      "test_start": test_start,
      "test_end": test_end,
      "metrics": metrics,
      "num_trades": metrics["num_trades"],
      "return_pct": metrics["total_return_pct"],
      "trades": trades,
    })
    oos_segments.append(equity)

  if oos_segments:
    oos_equity = pd.concat(oos_segments)
    oos_equity = oos_equity[~oos_equity.index.duplicated(keep="last")]
    all_trades = pd.concat(
      [w["trades"] for w in window_results if w.get("trades") is not None and len(w["trades"]) > 0],
      ignore_index=True,
    ) if window_results else pd.DataFrame()
    aggregate = compute_metrics(oos_equity, all_trades, BACKTEST.initial_cash)
  else:
    oos_equity = pd.Series(dtype=float)
    aggregate = compute_metrics(oos_equity, pd.DataFrame(), BACKTEST.initial_cash)

  return WalkForwardResult(
    windows=window_results,
    aggregate_metrics=aggregate,
    oos_equity=oos_equity,
  )


def print_walk_forward_summary(result: WalkForwardResult) -> None:
  print("=" * 60)
  print("WALK-FORWARD ANALYSIS (Out-of-Sample Windows)")
  print("=" * 60)
  for i, w in enumerate(result.windows, 1):
    print(
      f"Window {i}: test {w['test_start'].date()} → {w['test_end'].date()} | "
      f"Return: {w['return_pct']:.2f}% | Trades: {w['num_trades']}"
    )
  print("-" * 60)
  print("AGGREGATE OOS METRICS")
  print(format_metrics_table(result.aggregate_metrics))
  print("=" * 60)
