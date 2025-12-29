#!/usr/bin/env python3
"""
Setup verification script - checks if all dependencies and files are ready.
"""
import sys
import os
from pathlib import Path

def check_venv():
    """Check if running in virtual environment."""
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    return in_venv

def check_dependencies():
    """Check if required packages are installed."""
    required = [
        'pandas', 'numpy', 'backtesting',
        'binance', 'ta', 'dotenv'
    ]
    missing = []

    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)

    return missing

def check_files():
    """Check if required files exist."""
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
    for file in required_files:
        if not Path(file).exists():
            missing.append(file)

    return missing

def check_env():
    """Check if .env file exists."""
    return Path('.env').exists()

def main():
    print("="*60)
    print("TRADING SYSTEM SETUP VERIFICATION")
    print("="*60)

    # Check virtual environment
    print("\n1. Virtual Environment:")
    if check_venv():
        print("   ✓ Running in virtual environment")
    else:
        print("   ✗ NOT in virtual environment")
        print("   → Run: python3 -m venv venv && source venv/bin/activate")

    # Check dependencies
    print("\n2. Dependencies:")
    missing_deps = check_dependencies()
    if not missing_deps:
        print("   ✓ All dependencies installed")
    else:
        print(f"   ✗ Missing packages: {', '.join(missing_deps)}")
        print("   → Run: pip install -r requirements.txt")

    # Check files
    print("\n3. Required Files:")
    missing_files = check_files()
    if not missing_files:
        print("   ✓ All required files present")
    else:
        print(f"   ✗ Missing files:")
        for file in missing_files:
            print(f"     - {file}")

    # Check .env
    print("\n4. Environment Configuration:")
    if check_env():
        print("   ✓ .env file exists")
    else:
        print("   ✗ .env file not found")
        print("   → For live trading: cp .env.example .env")
        print("   → Then edit .env with your Binance Testnet API keys")

    # Final status
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
