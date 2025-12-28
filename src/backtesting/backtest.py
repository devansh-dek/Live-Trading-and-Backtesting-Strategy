from backtesting import Backtest
from src.strategy.multi_tf import MultiTFStrategy
import pandas as pd

def _prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Map lowercase column names to Backtesting.py expected names
    col_map = {
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close",
        "volume": "Volume",
    }
    for src, dst in col_map.items():
        if src in df.columns and dst not in df.columns:
            df[dst] = df[src]

    # Ensure datetime index
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])  # normalize if provided
        df = df.set_index("Date")
    elif "timestamp" in df.columns:
        df["Date"] = pd.to_datetime(df["timestamp"])  # from CSV
        df = df.set_index("Date")

    # Keep only required columns in correct order
    required = ["Open", "High", "Low", "Close", "Volume"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for Backtest: {missing}")
    return df[required]

def run_backtest(data: pd.DataFrame):
    df = _prepare_data(data)
    bt = Backtest(df, MultiTFStrategy, cash=10000)
    return bt.run()

from src.utils.logger import log_trade

def on_trade(trade):
    log_trade([
        trade.entry_time,
        trade.size,
        trade.entry_price,
        trade.exit_price,
        trade.pnl
    ], "data/backtest_trades.csv")
