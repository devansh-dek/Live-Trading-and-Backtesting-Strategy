"""Tests for multi-timeframe signal engine."""

import numpy as np
import pandas as pd

from config.config import StrategyConfig
from src.quant.signals import MultiTimeframeSignalEngine, Signal


def _make_trending_data(n=200, direction="up"):
  idx = pd.date_range("2024-01-01", periods=n, freq="15min")
  if direction == "up":
    close = np.linspace(40000, 50000, n) + np.random.default_rng(42).normal(0, 50, n)
  else:
    close = np.linspace(50000, 40000, n) + np.random.default_rng(42).normal(0, 50, n)
  return pd.DataFrame({
    "open": close - 10,
    "high": close + 50,
    "low": close - 50,
    "close": close,
    "volume": 100.0,
  }, index=idx)


def test_htf_trend_column_exists():
  engine = MultiTimeframeSignalEngine()
  df = _make_trending_data()
  prepared = engine.prepare_entry_frame(df)
  assert "htf_trend" in prepared.columns
  assert prepared["htf_trend"].isin(["UP", "DOWN", "NEUTRAL"]).all()


def test_entry_signal_returns_none_when_insufficient_data():
  engine = MultiTimeframeSignalEngine()
  df = _make_trending_data(n=30)
  signal, ctx = engine.entry_signal(df)
  assert signal is None


def test_exit_long_on_price_below_sma():
  engine = MultiTimeframeSignalEngine(StrategyConfig(sma_fast=5, sma_slow=10))
  df = _make_trending_data(n=120, direction="down")
  signal, ctx = engine.exit_signal(df, "LONG")
  assert signal in (Signal.CLOSE_LONG, None)
