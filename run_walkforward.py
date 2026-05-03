#!/usr/bin/env python3
"""Run walk-forward out-of-sample analysis."""

import argparse
import os

from src.backtesting.walk_forward import run_walk_forward, print_walk_forward_summary
from src.data.pipeline import load_or_fetch
from config.config import DATA_DIR


def main():
  parser = argparse.ArgumentParser(description="Walk-forward analysis")
  parser.add_argument("--fetch", action="store_true", help="Refresh historical data")
  args = parser.parse_args()

  path = os.path.join(DATA_DIR, "historical_data.csv")
  data = load_or_fetch(path, force=args.fetch)
  result = run_walk_forward(data)
  print_walk_forward_summary(result)


if __name__ == "__main__":
  main()
