#!/usr/bin/env python3
"""Verify project setup."""

import sys
from pathlib import Path


def main():
  print("=" * 60)
  print("QUANT TRADING SYSTEM — SETUP VERIFICATION")
  print("=" * 60)

  in_venv = hasattr(sys, "real_prefix") or (
    hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
  )
  print(f"\n1. Virtual env: {'OK' if in_venv else 'WARN (recommended)'}") 

  deps = ["pandas", "numpy", "backtesting", "binance", "matplotlib", "requests", "pytest"]
  missing = [p for p in deps if not _try_import(p)]
  print(f"2. Dependencies: {'OK' if not missing else 'MISSING: ' + ', '.join(missing)}")

  required = [
    "config/config.py",
    "src/quant/signals.py",
    "src/backtesting/backtest.py",
    "src/data/pipeline.py",
    "run_backtest.py",
    "run_walkforward.py",
  ]
  missing_files = [f for f in required if not Path(f).exists()]
  print(f"3. Project files: {'OK' if not missing_files else 'MISSING: ' + ', '.join(missing_files)}")

  has_env = Path(".env").exists()
  print(f"4. Live trading .env: {'OK' if has_env else 'Optional (copy .env.example)'}")

  data_ok = Path("data/historical_data.csv").exists()
  print(f"5. Historical data: {'OK' if data_ok else 'Run: make fetch-data'}")

  print("\n" + "=" * 60)
  if not missing and not missing_files:
    print("Ready. Run: make backtest | make walkforward | make test")
  else:
    print("Fix issues above, then: pip install -r requirements.txt")
  print("=" * 60)


def _try_import(pkg):
  try:
    __import__(pkg)
    return True
  except ImportError:
    return False


if __name__ == "__main__":
  main()
