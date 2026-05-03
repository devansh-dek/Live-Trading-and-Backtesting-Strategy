#!/usr/bin/env python3
"""Run full-period backtest with optional HTML report."""

import argparse

from src.backtesting.analyzer import print_stats
from src.backtesting.backtest import run_backtest
from src.data.pipeline import load_or_fetch
from config.config import DATA_DIR
import os


def main():
  parser = argparse.ArgumentParser(description="Run strategy backtest")
  parser.add_argument("--report", action="store_true", help="Generate HTML report")
  parser.add_argument("--fetch", action="store_true", help="Refresh historical data")
  args = parser.parse_args()

  path = os.path.join(DATA_DIR, "historical_data.csv")
  data = load_or_fetch(path, force=args.fetch)
  result = run_backtest(data, generate_html_report=args.report)
  print_stats(result)


if __name__ == "__main__":
  main()
