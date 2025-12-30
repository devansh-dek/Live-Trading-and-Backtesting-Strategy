# src/backtesting/backtest.py
import os
import pandas as pd
from backtesting import Backtest
from src.strategy.multi_tf import MultiTFStrategy
import warnings
warnings.filterwarnings("ignore")

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)


def _prepare_data(df):
    df = df.copy()

    # Map column names to standard format
    rename = {}
    for c in df.columns:
        cl = c.lower().strip()
        if cl == "open":
            rename[c] = "Open"
        elif cl == "high":
            rename[c] = "High"
        elif cl == "low":
            rename[c] = "Low"
        elif cl == "close":
            rename[c] = "Close"
        elif cl in ("volume", "vol"):
            rename[c] = "Volume"
        elif cl in ("date", "timestamp", "datetime"):
            rename[c] = "Date"

    df.rename(columns=rename, inplace=True)

    # Add volume if missing
    if "Volume" not in df.columns:
        df["Volume"] = 1000

    # Handle date index
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])
        df.set_index("Date", inplace=True)
    else:
        # fallback if no date column
        df.index = pd.date_range("2024-01-01", periods=len(df), freq="15min")

    # Verify we have everything
    required = ["Open", "High", "Low", "Close", "Volume"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    return df[required]


def run_backtest(data):
    df = _prepare_data(data)

    bt = Backtest(
        df,
        MultiTFStrategy,
        cash=100_000,
        commission=0.002,
        trade_on_close=True,
        exclusive_orders=True,
        finalize_trades=True,
    )

    results = bt.run()

    # Save trades if any
    trades = getattr(results, "_trades", None)
    out = os.path.join(DATA_DIR, "backtest_trades.csv")

    if trades is not None and len(trades) > 0:
        trades.to_csv(out, index=False)
        print(f"Saved {len(trades)} trades → {out}")
    else:
        print("No trades generated")
        # save empty file anyway
        pd.DataFrame().to_csv(out, index=False)

    return results