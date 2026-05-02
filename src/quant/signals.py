"""Multi-timeframe signal engine — shared by backtest and live trading."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

import numpy as np
import pandas as pd

from config.config import StrategyConfig, STRATEGY
from src.quant.indicators import add_indicators


class Signal(str, Enum):
  BUY = "BUY"
  SELL = "SELL"
  CLOSE_LONG = "CLOSE_LONG"
  CLOSE_SHORT = "CLOSE_SHORT"
  HOLD = "HOLD"


@dataclass
class SignalContext:
  timestamp: pd.Timestamp
  price: float
  rsi: float
  rsi_delta: float
  sma_fast: float
  sma_slow: float
  atr: float
  htf_trend: str  # "UP", "DOWN", "NEUTRAL"
  reason: str


@dataclass
class MultiTimeframeSignalEngine:
  """
  Entry logic (15m):
    - Long when 1h trend is UP and 15m RSI momentum is positive
    - Short when 1h trend is DOWN and 15m RSI momentum is negative

  Exit logic (15m):
    - Long exit when price closes below fast SMA
    - Short exit when price closes above fast SMA

  The 1h trend filter is computed by resampling 15m bars to 1h and applying
  SMA crossover — this is the defensible multi-timeframe design.
  """

  config: StrategyConfig = STRATEGY

  def prepare_entry_frame(self, df_15m: pd.DataFrame) -> pd.DataFrame:
    df = add_indicators(
      df_15m,
      rsi_period=self.config.rsi_period,
      sma_fast=self.config.sma_fast,
      sma_slow=self.config.sma_slow,
      atr_period=self.config.atr_period,
    )
    df["htf_trend"] = self._compute_htf_trend(df)
    return df

  def _compute_htf_trend(self, df_15m: pd.DataFrame) -> pd.Series:
    """Resample 15m → 1h, compute SMA trend, forward-fill to 15m bars."""
    df = df_15m.copy()
    df.columns = [c.lower() for c in df.columns]
    if not isinstance(df.index, pd.DatetimeIndex):
      if "timestamp" in df.columns:
        df = df.set_index("timestamp")
      else:
        raise ValueError("DataFrame needs DatetimeIndex or 'timestamp' column")

    ohlc = df[["open", "high", "low", "close"]].resample("1h").agg(
      {"open": "first", "high": "max", "low": "min", "close": "last"}
    ).dropna()

    htf = add_indicators(
      ohlc,
      rsi_period=self.config.rsi_period,
      sma_fast=self.config.sma_fast,
      sma_slow=self.config.sma_slow,
      atr_period=self.config.atr_period,
    )

    trend = pd.Series("NEUTRAL", index=htf.index)
    trend[htf["sma_fast"] > htf["sma_slow"]] = "UP"
    trend[htf["sma_fast"] < htf["sma_slow"]] = "DOWN"

    return trend.reindex(df.index, method="ffill").fillna("NEUTRAL")

  def entry_signal(self, df_15m: pd.DataFrame, position: Optional[str] = None) -> tuple[Optional[Signal], Optional[SignalContext]]:
    if position is not None:
      return None, None

    df = self.prepare_entry_frame(df_15m)
    if len(df) < self.config.sma_slow:
      return None, None

    row = df.iloc[-1]
    if row[["close", "rsi", "rsi_delta", "sma_fast", "sma_slow", "atr"]].isna().any():
      return None, None

    ctx = SignalContext(
      timestamp=df.index[-1] if isinstance(df.index, pd.DatetimeIndex) else pd.Timestamp.now(),
      price=float(row["close"]),
      rsi=float(row["rsi"]),
      rsi_delta=float(row["rsi_delta"]),
      sma_fast=float(row["sma_fast"]),
      sma_slow=float(row["sma_slow"]),
      atr=float(row["atr"]),
      htf_trend=str(row["htf_trend"]),
      reason="",
    )

    momentum_up = ctx.rsi_delta >= self.config.rsi_momentum
    momentum_down = ctx.rsi_delta <= -self.config.rsi_momentum

    if ctx.htf_trend == "UP" and momentum_up:
      ctx.reason = f"1h UP trend + RSI momentum +{ctx.rsi_delta:.1f}"
      return Signal.BUY, ctx

    if ctx.htf_trend == "DOWN" and momentum_down:
      ctx.reason = f"1h DOWN trend + RSI momentum {ctx.rsi_delta:.1f}"
      return Signal.SELL, ctx

    return None, ctx

  def exit_signal(self, df_15m: pd.DataFrame, position: str) -> tuple[Optional[Signal], Optional[SignalContext]]:
    df = self.prepare_entry_frame(df_15m)
    if len(df) < self.config.sma_fast:
      return None, None

    row = df.iloc[-1]
    if row[["close", "sma_fast"]].isna().any():
      return None, None

    ctx = SignalContext(
      timestamp=df.index[-1] if isinstance(df.index, pd.DatetimeIndex) else pd.Timestamp.now(),
      price=float(row["close"]),
      rsi=float(row.get("rsi", np.nan)),
      rsi_delta=float(row.get("rsi_delta", np.nan)),
      sma_fast=float(row["sma_fast"]),
      sma_slow=float(row.get("sma_slow", np.nan)),
      atr=float(row.get("atr", np.nan)),
      htf_trend=str(row.get("htf_trend", "NEUTRAL")),
      reason="",
    )

    if position == "LONG" and ctx.price < ctx.sma_fast:
      ctx.reason = f"Price {ctx.price:.2f} < SMA{self.config.sma_fast} {ctx.sma_fast:.2f}"
      return Signal.CLOSE_LONG, ctx

    if position == "SHORT" and ctx.price > ctx.sma_fast:
      ctx.reason = f"Price {ctx.price:.2f} > SMA{self.config.sma_fast} {ctx.sma_fast:.2f}"
      return Signal.CLOSE_SHORT, ctx

    return None, ctx

  def stop_loss(self, entry_price: float, atr_value: float, side: str) -> float:
    if side in ("BUY", "LONG"):
      return entry_price - self.config.atr_sl_mult * atr_value
    return entry_price + self.config.atr_sl_mult * atr_value

  def take_profit(self, entry_price: float, atr_value: float, side: str) -> float:
    if side in ("BUY", "LONG"):
      return entry_price + self.config.atr_tp_mult * atr_value
    return entry_price - self.config.atr_tp_mult * atr_value
