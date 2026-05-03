"""Performance metrics for backtests and walk-forward analysis."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd


def compute_metrics(
  equity_curve: pd.Series,
  trades: pd.DataFrame,
  initial_cash: float,
  risk_free_rate: float = 0.0,
) -> dict[str, Any]:
  if equity_curve.empty:
    return _empty_metrics(initial_cash)

  returns = equity_curve.pct_change().dropna()
  total_return = (equity_curve.iloc[-1] / initial_cash - 1) * 100

  n_trades = len(trades) if trades is not None else 0
  wins = int((trades["PnL"] > 0).sum()) if n_trades else 0
  win_rate = (wins / n_trades * 100) if n_trades else 0.0

  max_dd = _max_drawdown(equity_curve) * 100
  sharpe = _sharpe(returns, risk_free_rate)
  sortino = _sortino(returns, risk_free_rate)
  calmar = (total_return / max_dd) if max_dd > 0 else np.nan

  profit_factor = np.nan
  avg_trade = np.nan
  if n_trades:
    gross_profit = trades.loc[trades["PnL"] > 0, "PnL"].sum()
    gross_loss = abs(trades.loc[trades["PnL"] < 0, "PnL"].sum())
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else np.inf
    avg_trade = trades["PnL"].mean()

  return {
    "total_return_pct": round(total_return, 2),
    "final_equity": round(float(equity_curve.iloc[-1]), 2),
    "max_drawdown_pct": round(max_dd, 2),
    "sharpe_ratio": _round_or_nan(sharpe),
    "sortino_ratio": _round_or_nan(sortino),
    "calmar_ratio": _round_or_nan(calmar),
    "num_trades": n_trades,
    "win_rate_pct": round(win_rate, 2),
    "profit_factor": _round_or_nan(profit_factor),
    "avg_trade_pnl": _round_or_nan(avg_trade),
    "exposure_pct": _exposure_pct(trades, equity_curve),
  }


def benchmark_buy_hold(prices: pd.Series, initial_cash: float) -> dict[str, float]:
  if prices.empty:
    return {"total_return_pct": 0.0, "final_equity": initial_cash}
  qty = initial_cash / prices.iloc[0]
  final = qty * prices.iloc[-1]
  return {
    "total_return_pct": round((final / initial_cash - 1) * 100, 2),
    "final_equity": round(final, 2),
  }


def _max_drawdown(equity: pd.Series) -> float:
  peak = equity.cummax()
  dd = (equity - peak) / peak
  return abs(dd.min())


def _sharpe(returns: pd.Series, rf: float, periods_per_year: int = 252 * 24 * 4) -> float:
  if returns.std() == 0 or len(returns) < 2:
    return np.nan
  excess = returns - rf / periods_per_year
  return float(excess.mean() / excess.std() * math.sqrt(periods_per_year))


def _sortino(returns: pd.Series, rf: float, periods_per_year: int = 252 * 24 * 4) -> float:
  downside = returns[returns < 0]
  if len(downside) == 0 or downside.std() == 0:
    return np.nan
  excess = returns - rf / periods_per_year
  downside_std = downside.std()
  return float(excess.mean() / downside_std * math.sqrt(periods_per_year))


def _exposure_pct(trades: pd.DataFrame, equity: pd.Series) -> float:
  if trades is None or trades.empty or equity.empty:
    return 0.0
  if "Duration" not in trades.columns:
    return np.nan
  total_bars = len(equity)
  duration = trades["Duration"]
  if pd.api.types.is_timedelta64_dtype(duration):
    in_market = duration.dt.total_seconds().sum()
    bar_seconds = 900  # 15m bars
    return round(in_market / bar_seconds / total_bars * 100, 2) if total_bars else 0.0
  in_market = duration.sum()
  return round(in_market / total_bars * 100, 2) if total_bars else 0.0


def _round_or_nan(val: float) -> float | str:
  if val is None or (isinstance(val, float) and (math.isnan(val) or math.isinf(val))):
    return "N/A"
  return round(float(val), 3)


def _empty_metrics(initial_cash: float) -> dict[str, Any]:
  return {
    "total_return_pct": 0.0,
    "final_equity": initial_cash,
    "max_drawdown_pct": 0.0,
    "sharpe_ratio": "N/A",
    "sortino_ratio": "N/A",
    "calmar_ratio": "N/A",
    "num_trades": 0,
    "win_rate_pct": 0.0,
    "profit_factor": "N/A",
    "avg_trade_pnl": "N/A",
    "exposure_pct": 0.0,
  }


def format_metrics_table(metrics: dict[str, Any], label: str = "Strategy") -> str:
  lines = [
    f"{'Metric':<22} {label:>14}",
    "-" * 38,
  ]
  mapping = [
    ("Total Return %", "total_return_pct"),
    ("Final Equity $", "final_equity"),
    ("Max Drawdown %", "max_drawdown_pct"),
    ("Sharpe Ratio", "sharpe_ratio"),
    ("Sortino Ratio", "sortino_ratio"),
    ("Calmar Ratio", "calmar_ratio"),
    ("Trades", "num_trades"),
    ("Win Rate %", "win_rate_pct"),
    ("Profit Factor", "profit_factor"),
    ("Avg Trade PnL", "avg_trade_pnl"),
    ("Exposure %", "exposure_pct"),
  ]
  for name, key in mapping:
    val = metrics.get(key, "N/A")
    if isinstance(val, float):
      lines.append(f"{name:<22} {val:>14.2f}")
    else:
      lines.append(f"{name:<22} {val:>14}")
  return "\n".join(lines)
