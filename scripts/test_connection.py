#!/usr/bin/env python3
"""Verify Binance Testnet API connection without starting the trading loop."""

import sys

from config.config import SYMBOL
from src.trading.exchange import BinanceExchange


def main():
  print("=" * 60)
  print("BINANCE TESTNET CONNECTION CHECK")
  print("=" * 60)

  exchange = BinanceExchange()
  price = exchange.get_current_price()
  auth = exchange.is_authenticated()
  usdt = exchange.get_account_balance("USDT")
  btc = exchange.get_account_balance("BTC")

  print(f"Symbol:        {SYMBOL}")
  print(f"Price:         ${price:,.2f}" if price else "Price:         FAILED")
  print(f"Authenticated: {'YES' if auth else 'NO'}")
  print(f"USDT Balance:  ${usdt:,.2f}")
  print(f"BTC Balance:   {btc:.8f}")
  print("=" * 60)

  if price is None or not auth:
    print("FAILED — check API keys in .env (must be testnet keys)")
    sys.exit(1)

  print("SUCCESS — testnet connection is working")
  return 0


if __name__ == "__main__":
  sys.exit(main() or 0)
