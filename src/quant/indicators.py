"""Vectorized technical indicators used by the signal engine."""

from __future__ import annotations

import numpy as np
import pandas as pd


def sma(series: pd.Series, period: int) -> pd.Series:
  return series.rolling(window=period, min_periods=period).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
  delta = series.diff()
  gain = delta.clip(lower=0)
  loss = -delta.clip(upper=0)
  avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
  avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
  rs = avg_gain / avg_loss.replace(0, np.nan)
  return 100 - (100 / (1 + rs))


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
  prev_close = close.shift(1)
  tr = pd.concat(
    [
      high - low,
      (high - prev_close).abs(),
      (low - prev_close).abs(),
    ],
    axis=1,
  ).max(axis=1)
  return tr.rolling(window=period, min_periods=period).mean()


def add_indicators(
  df: pd.DataFrame,
  *,
  rsi_period: int = 14,
  sma_fast: int = 20,
  sma_slow: int = 60,
  atr_period: int = 14,
) -> pd.DataFrame:
  """Add standard indicator columns to an OHLCV dataframe."""
  out = df.copy()
  out.columns = [c.lower() for c in out.columns]
  close = out["close"]
  out["rsi"] = rsi(close, rsi_period)
  out["sma_fast"] = sma(close, sma_fast)
  out["sma_slow"] = sma(close, sma_slow)
  out["atr"] = atr(out["high"], out["low"], close, atr_period)
  out["rsi_delta"] = out["rsi"].diff()
  return out
