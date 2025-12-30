# src/backtesting/backtest.py
import os
import pandas as pd
from backtesting import Backtest
from src.strategy.multi_tf import MultiTFStrategy
import warnings
warnings.filterwarnings("ignore")

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)


def _prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()


    # Normalize column names
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


    if "Volume" not in df.columns:
        df["Volume"] = 1000
       

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])
        df.set_index("Date", inplace=True)
    else:
        df.index = pd.date_range("2024-01-01", periods=len(df), freq="15min")
      

    required = ["Open", "High", "Low", "Close", "Volume"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    df = df[required]
    return df


def run_backtest(data: pd.DataFrame):

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

    trades = getattr(results, "_trades", None)
    out = os.path.join(DATA_DIR, "backtest_trades.csv")

    if trades is not None and len(trades) > 0:
        trades.to_csv(out, index=False)
        print(f"Saved {len(trades)} trades → {out}")
    else:
        print("No trades generated")
        trades = pd.DataFrame()
        trades.to_csv(out, index=False)


    return results
