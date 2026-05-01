import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class StrategyConfig:
  """Strategy parameters — single source of truth for backtest and live."""

  symbol: str = "BTCUSDT"
  entry_timeframe: str = "15m"
  confirm_timeframe: str = "1h"

  rsi_period: int = 14
  rsi_momentum: float = 2.0
  sma_fast: int = 20
  sma_slow: int = 60
  atr_period: int = 14
  atr_sl_mult: float = 1.5
  atr_tp_mult: float = 2.5

  # Risk
  risk_per_trade: float = 0.01
  max_daily_loss_pct: float = 0.03
  max_position_pct: float = 0.25


@dataclass(frozen=True)
class BacktestConfig:
  initial_cash: float = 100_000.0
  commission: float = 0.001
  slippage_bps: float = 5.0
  trade_on_close: bool = True


@dataclass(frozen=True)
class WalkForwardConfig:
  train_months: int = 6
  test_months: int = 1
  min_trades_per_window: int = 3


# Module-level defaults
STRATEGY = StrategyConfig()
BACKTEST = BacktestConfig()
WALK_FORWARD = WalkForwardConfig()

SYMBOL = STRATEGY.symbol
ENTRY_TIMEFRAME = STRATEGY.entry_timeframe
CONFIRM_TIMEFRAME = STRATEGY.confirm_timeframe
RISK_PER_TRADE = STRATEGY.risk_per_trade

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

DATA_DIR = "data"
REPORTS_DIR = "reports"
LOGS_DIR = "logs"
DB_PATH = os.path.join(DATA_DIR, "trading_journal.db")
