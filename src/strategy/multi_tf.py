"""Multi-timeframe strategy — thin wrapper around the shared signal engine."""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from backtesting import Strategy

from config.config import STRATEGY
from src.quant.signals import MultiTimeframeSignalEngine, Signal

logger = logging.getLogger(__name__)

_HTF_UP = 1.0
_HTF_DOWN = -1.0
_HTF_NEUTRAL = 0.0


class MultiTFStrategy(Strategy):
  """
  Backtesting.py adapter for MultiTimeframeSignalEngine.

  Indicators are precomputed once in init() for O(n) backtests on large datasets.
  """

  rsi_period = STRATEGY.rsi_period
  sma_fast = STRATEGY.sma_fast
  sma_slow = STRATEGY.sma_slow
  rsi_momentum = STRATEGY.rsi_momentum
  atr_period = STRATEGY.atr_period
  atr_sl = STRATEGY.atr_sl_mult
  atr_tp = STRATEGY.atr_tp_mult

  def init(self):
    from config.config import StrategyConfig

    cfg = StrategyConfig(
      rsi_period=self.rsi_period,
      sma_fast=self.sma_fast,
      sma_slow=self.sma_slow,
      rsi_momentum=self.rsi_momentum,
      atr_period=self.atr_period,
      atr_sl_mult=self.atr_sl,
      atr_tp_mult=self.atr_tp,
    )
    self.engine = MultiTimeframeSignalEngine(cfg)

    df = self._to_frame()
    prepared = self.engine.prepare_entry_frame(df)

    trend_map = {"UP": _HTF_UP, "DOWN": _HTF_DOWN, "NEUTRAL": _HTF_NEUTRAL}
    htf_vals = prepared["htf_trend"].map(trend_map).to_numpy(dtype=float)

    self.rsi_line = self.I(lambda _: prepared["rsi"].to_numpy(), self.data.Close)
    self.sma_fast_line = self.I(lambda _: prepared["sma_fast"].to_numpy(), self.data.Close)
    self.sma_slow_line = self.I(lambda _: prepared["sma_slow"].to_numpy(), self.data.Close)
    self.atr_line = self.I(lambda _: prepared["atr"].to_numpy(), self.data.Close)
    self.htf_line = self.I(lambda _: htf_vals, self.data.Close)

  def _to_frame(self) -> pd.DataFrame:
    idx = self.data.index
    return pd.DataFrame(
      {
        "open": self.data.Open,
        "high": self.data.High,
        "low": self.data.Low,
        "close": self.data.Close,
        "volume": self.data.Volume,
      },
      index=idx,
    )

  def next(self):
    if len(self.data.Close) < self.sma_slow:
      return

    close = float(self.data.Close[-1])
    rsi_now = float(self.rsi_line[-1])
    rsi_prev = float(self.rsi_line[-2])
    sma_fast = float(self.sma_fast_line[-1])
    htf = float(self.htf_line[-1])
    atr = float(self.atr_line[-1])

    if np.isnan([rsi_now, rsi_prev, sma_fast, atr, htf]).any():
      return

    if self.position:
      if self.position.is_long and close < sma_fast:
        self.position.close()
        return
      if self.position.is_short and close > sma_fast:
        self.position.close()
        return

    if not self.position:
      momentum_up = rsi_now - rsi_prev >= self.rsi_momentum
      momentum_down = rsi_prev - rsi_now >= self.rsi_momentum

      if htf == _HTF_UP and momentum_up:
        self.buy(sl=close - self.atr_sl * atr, tp=close + self.atr_tp * atr)
      elif htf == _HTF_DOWN and momentum_down:
        self.sell(sl=close + self.atr_sl * atr, tp=close - self.atr_tp * atr)

  def generate_entry_signal(self, df):
    signal, _ = self.engine.entry_signal(df)
    if signal == Signal.BUY:
      return "BUY"
    if signal == Signal.SELL:
      return "SELL"
    return None

  def generate_exit_signal(self, df, position=None):
    if position is None:
      return None
    signal, _ = self.engine.exit_signal(df, position)
    if signal == Signal.CLOSE_LONG:
      return "CLOSE_LONG"
    if signal == Signal.CLOSE_SHORT:
      return "CLOSE_SHORT"
    return None

  def get_stop_loss(self, df, entry_price, side):
    prepared = self.engine.prepare_entry_frame(df)
    atr_val = float(prepared["atr"].iloc[-1]) if len(prepared) else entry_price * 0.02
    return self.engine.stop_loss(entry_price, atr_val, side)

  def get_take_profit(self, df, entry_price, side):
    prepared = self.engine.prepare_entry_frame(df)
    atr_val = float(prepared["atr"].iloc[-1]) if len(prepared) else entry_price * 0.02
    return self.engine.take_profit(entry_price, atr_val, side)
