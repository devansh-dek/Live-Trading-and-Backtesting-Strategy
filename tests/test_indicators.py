"""Tests for technical indicators."""

import numpy as np
import pandas as pd
import pytest

from src.quant.indicators import add_indicators, rsi, sma, atr


@pytest.fixture
def ohlcv():
  n = 100
  idx = pd.date_range("2024-01-01", periods=n, freq="15min")
  close = pd.Series(np.linspace(100, 120, n) + np.random.randn(n) * 0.5, index=idx)
  return pd.DataFrame({
    "open": close - 0.1,
    "high": close + 0.5,
    "low": close - 0.5,
    "close": close,
    "volume": 1000.0,
  }, index=idx)


def test_sma_length(ohlcv):
  result = sma(ohlcv["close"], 20)
  assert result.notna().sum() == len(ohlcv) - 19


def test_rsi_bounded(ohlcv):
  result = rsi(ohlcv["close"], 14)
  valid = result.dropna()
  assert valid.min() >= 0
  assert valid.max() <= 100


def test_atr_positive(ohlcv):
  result = atr(ohlcv["high"], ohlcv["low"], ohlcv["close"], 14)
  valid = result.dropna()
  assert (valid > 0).all()


def test_add_indicators_columns(ohlcv):
  out = add_indicators(ohlcv)
  for col in ["rsi", "sma_fast", "sma_slow", "atr", "rsi_delta"]:
    assert col in out.columns
