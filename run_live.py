#!/usr/bin/env python3
"""Live trading orchestrator — delegates all logic to LiveRunner + signal engine."""

import logging
import sys

from config.config import ENTRY_TIMEFRAME, SYMBOL
from src.trading.exchange import BinanceExchange
from src.trading.live_runner import LiveRunner

logging.basicConfig(
  level=logging.INFO,
  format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
  handlers=[
    logging.FileHandler("trading.log"),
    logging.StreamHandler(),
  ],
)
logger = logging.getLogger(__name__)


def main():
  logger.info("=" * 70)
  logger.info("LIVE TRADING — Binance Testnet")
  logger.info("=" * 70)

  try:
    exchange = BinanceExchange()
    price = exchange.get_current_price()
    if price is None or not exchange.is_authenticated():
      raise RuntimeError("Binance Testnet unavailable or API keys invalid")

    balance = exchange.get_account_balance("USDT")
    logger.info("Connected | %s @ $%s | USDT: $%s", SYMBOL, f"{price:,.2f}", f"{balance:,.2f}")

    print("\nPress Ctrl+C to stop\n")
    LiveRunner(exchange=exchange).run(
      symbol=SYMBOL,
      timeframe=ENTRY_TIMEFRAME,
      fetch_limit=120,
      loop_delay=60,
    )

  except Exception as exc:
    logger.error("Live trading error: %s", exc, exc_info=True)
    sys.exit(1)


if __name__ == "__main__":
  main()
