#!/usr/bin/env python3
import sys
import os
from pathlib import Path

def check_venv():
    # Check if we're in a venv
    return hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )

def check_dependencies():
    required = [
        'pandas', 'numpy', 'backtesting',
        'binance', 'ta', 'dotenv'
    ]
    missing = []

    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    return missing

def check_files():
    required_files = [
        'config/config.py',
        'src/strategy/multi_tf.py',
        'src/backtesting/backtest.py',
        'src/backtesting/analyzer.py',
        'src/trading/exchange.py',
        'src/trading/executor.py',
        'data/historical_data.csv',
        'run_backtest.py',
        'run_live.py'
    ]

    missing = []
    for f in required_files:
        if not Path(f).exists():
            missing.append(f)

    return missing

def main():
    print("="*60)
    print("TRADING SYSTEM SETUP VERIFICATION")
    print("="*60)

    # Virtual environment check
    print("\n1. Virtual Environment:")
    if check_venv():
        print("   ✓ Running in virtual environment")
    else:
        print("   ✗ NOT in virtual environment")
        print("   → Run: python3 -m venv venv && source venv/bin/activate")

    # Dependencies
    print("\n2. Dependencies:")
    missing_deps = check_dependencies()
    if not missing_deps:
        print("   ✓ All dependencies installed")
    else:
        print(f"   ✗ Missing packages: {', '.join(missing_deps)}")
        print("   → Run: pip install -r requirements.txt")

    # Files
    print("\n3. Required Files:")
    missing_files = check_files()
    if not missing_files:
        print("   ✓ All required files present")
    else:
        print(f"   ✗ Missing files:")
        for f in missing_files:
            print(f"     - {f}")

    # Env config
    print("\n4. Environment Configuration:")
    if Path('.env').exists():
        print("   ✓ .env file exists")
    else:
        print("   ✗ .env file not found")
        print("   → For live trading: cp .env.example .env")
        print("   → Then edit .env with your Binance Testnet API keys")

    # Summary
    print("\n" + "="*60)
    if not missing_deps and not missing_files and check_venv():
        print("✓ SETUP COMPLETE - Ready to run backtest!")
        print("\nNext steps:")
        print("  python run_backtest.py")
        print("\nFor live trading setup:")
        print("  1. Get testnet keys from https://testnet.binance.vision/")
        print("  2. Copy .env.example to .env and add your keys")
        print("  3. Run: python run_live.py")
    else:
        print("✗ SETUP INCOMPLETE - Please address issues above")
    print("="*60)

if __name__ == "__main__":
    main()