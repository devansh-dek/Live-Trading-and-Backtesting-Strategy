"""Backtesting engine wrapping backtesting.py with unified strategy."""

from __future__ import annotations

import os
from typing import Type

import pandas as pd
from backtesting import Backtest

from config.config import BACKTEST, DATA_DIR, StrategyConfig, STRATEGY
from src.backtesting.metrics import benchmark_buy_hold, compute_metrics
from src.backtesting.report import generate_report
from src.data.pipeline import normalize_ohlcv
from src.strategy.multi_tf import MultiTFStrategy
import warnings

warnings.filterwarnings("ignore")

os.makedirs(DATA_DIR, exist_ok=True)


def prepare_backtest_data(df: pd.DataFrame) -> pd.DataFrame:
  """Convert OHLCV to backtesting.py format (capitalized columns, DatetimeIndex)."""
  df = normalize_ohlcv(df)
  out = df.rename(columns={
    "open": "Open",
    "high": "High",
    "low": "Low",
    "close": "Close",
    "volume": "Volume",
  })
  return out


def get_strategy_class(config: StrategyConfig | None = None) -> Type[MultiTFStrategy]:
  cfg = config or STRATEGY

  class ConfiguredStrategy(MultiTFStrategy):
    rsi_period = cfg.rsi_period
    sma_fast = cfg.sma_fast
    sma_slow = cfg.sma_slow
    rsi_momentum = cfg.rsi_momentum
    atr_period = cfg.atr_period
    atr_sl = cfg.atr_sl_mult
    atr_tp = cfg.atr_tp_mult

  return ConfiguredStrategy


def run_backtest(
  data: pd.DataFrame,
  *,
  generate_html_report: bool = False,
  strategy_config: StrategyConfig | None = None,
) -> dict:
  df = prepare_backtest_data(data)
  StrategyClass = get_strategy_class(strategy_config)

  bt = Backtest(
    df,
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
  benchmark = benchmark_buy_hold(df["Close"], BACKTEST.initial_cash)

  out_path = os.path.join(DATA_DIR, "backtest_trades.csv")
  if trades is not None and len(trades) > 0:
    trades.to_csv(out_path, index=False)
  else:
    pd.DataFrame().to_csv(out_path, index=False)

  report_path = None
  if generate_html_report:
    report_path = generate_report(equity, trades, metrics, benchmark)

  return {
    "stats": stats,
    "trades": trades,
    "equity": equity,
    "metrics": metrics,
    "benchmark": benchmark,
    "report_path": report_path,
  }
