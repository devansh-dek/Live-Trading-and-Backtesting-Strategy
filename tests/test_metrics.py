"""Tests for performance metrics."""

import pandas as pd
import pytest

from src.backtesting.metrics import compute_metrics, benchmark_buy_hold


def test_benchmark_buy_hold():
  prices = pd.Series([100, 110, 105], index=pd.date_range("2024-01-01", periods=3, freq="D"))
  result = benchmark_buy_hold(prices, 10_000)
  assert result["total_return_pct"] == 5.0
  assert result["final_equity"] == 10_500


def test_compute_metrics_basic():
  equity = pd.Series([100_000, 101_000, 100_500, 102_000])
  trades = pd.DataFrame({"PnL": [500, -200, 800], "Duration": [10, 5, 15]})
  m = compute_metrics(equity, trades, 100_000)
  assert m["num_trades"] == 3
  assert m["total_return_pct"] == 2.0
  assert m["win_rate_pct"] == pytest.approx(66.67, rel=0.01)
