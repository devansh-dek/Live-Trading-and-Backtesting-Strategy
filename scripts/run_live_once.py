#!/usr/bin/env python3
"""Run one live trading iteration to verify end-to-end signal + journal pipeline."""

import logging
import sys

from config.config import ENTRY_TIMEFRAME, SYMBOL
from src.trading.exchange import BinanceExchange
from src.trading.live_runner import LiveRunner

logging.basicConfig(
  level=logging.INFO,
  format="%(asctime)s - %(levelname)s - %(message)s",
  handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def main():
  exchange = BinanceExchange()
  if not exchange.is_authenticated():
    logger.error("Testnet auth failed — check .env keys")
    sys.exit(1)

  logger.info("Running 1 live iteration (signal-driven only, no forced trades)")
  LiveRunner(exchange=exchange).run(
    symbol=SYMBOL,
    timeframe=ENTRY_TIMEFRAME,
    fetch_limit=120,
    loop_delay=1,
    max_iterations=1,
  )
  logger.info("Live iteration complete")


if __name__ == "__main__":
  main()
