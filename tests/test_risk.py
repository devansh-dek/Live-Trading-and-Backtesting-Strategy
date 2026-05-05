"""Tests for risk management."""

from datetime import date

from src.quant.risk import RiskManager
from config.config import StrategyConfig


def test_position_size_respects_max_position():
  rm = RiskManager(StrategyConfig(risk_per_trade=0.05, max_position_pct=0.10))
  qty = rm.position_size(equity=100_000, entry_price=50_000, stop_loss=49_000)
  max_qty = (100_000 * 0.10) / 50_000
  assert qty <= max_qty + 1e-9


def test_daily_loss_breach():
  rm = RiskManager(StrategyConfig(max_daily_loss_pct=0.03))
  today = date(2024, 6, 1)
  rm.record_pnl(today, -4000)
  assert rm.is_daily_loss_breached(100_000, today) is True


def test_zero_risk_per_unit_returns_zero():
  rm = RiskManager()
  assert rm.position_size(100_000, 50_000, 50_000) == 0.0
