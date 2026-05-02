"""Position sizing and risk controls."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from config.config import StrategyConfig, STRATEGY


@dataclass
class RiskManager:
  config: StrategyConfig = STRATEGY
  daily_pnl: dict[date, float] = field(default_factory=dict)

  def position_size(
    self,
    equity: float,
    entry_price: float,
    stop_loss: float,
  ) -> float:
    """
    Fixed fractional risk sizing: risk a fixed % of equity per trade
    based on distance to stop loss.
    """
    if entry_price <= 0 or equity <= 0:
      return 0.0

    risk_amount = equity * self.config.risk_per_trade
    risk_per_unit = abs(entry_price - stop_loss)
    if risk_per_unit <= 0:
      return 0.0

    qty = risk_amount / risk_per_unit
    max_qty = (equity * self.config.max_position_pct) / entry_price
    return min(qty, max_qty)

  def record_pnl(self, trade_date: date, pnl: float) -> None:
    self.daily_pnl[trade_date] = self.daily_pnl.get(trade_date, 0.0) + pnl

  def is_daily_loss_breached(self, equity: float, trade_date: date) -> bool:
    daily = self.daily_pnl.get(trade_date, 0.0)
    limit = -equity * self.config.max_daily_loss_pct
    return daily <= limit
