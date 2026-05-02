#!/usr/bin/env python3
"""Download historical OHLCV data from Binance public API."""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import DATA_DIR, SYMBOL, ENTRY_TIMEFRAME
from src.data.pipeline import load_or_fetch


def main():
  parser = argparse.ArgumentParser(description="Fetch historical klines from Binance")
  parser.add_argument("--symbol", default=SYMBOL)
  parser.add_argument("--interval", default=ENTRY_TIMEFRAME)
  parser.add_argument("--months", type=int, default=18)
  parser.add_argument("--force", action="store_true", help="Re-download even if cached")
  args = parser.parse_args()

  path = os.path.join(DATA_DIR, "historical_data.csv")
  df = load_or_fetch(
    path,
    symbol=args.symbol,
    interval=args.interval,
    months=args.months,
    force=args.force,
  )
  print(f"Saved {len(df):,} bars → {path}")
  print(f"Range: {df.index[0]} → {df.index[-1]}")


if __name__ == "__main__":
  main()
