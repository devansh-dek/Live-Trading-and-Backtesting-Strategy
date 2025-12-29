#!/usr/bin/env python3
"""
Live trading script for multi-timeframe strategy on Binance Testnet.
WARNING: This will execute real orders on Binance Testnet.
"""

from src.trading.exchange import BinanceExchange
from src.trading.executor import TradeExecutor
from src.utils.logger import log_trade
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("="*60)
    logger.info("Starting Live Trading System")
    logger.info("="*60)

    try:
        # Initialize exchange and executor. If Testnet keys are missing or invalid,
        # fall back to a simulated exchange so the runner still operates in "simulation" mode.
        try:
            exchange = BinanceExchange()
            # Quick connectivity + authentication check
            price = exchange.get_current_price()
            auth_ok = getattr(exchange, 'is_authenticated', lambda: False)()
            balance = exchange.get_account_balance("USDT")
            if price is None or not auth_ok:
                raise RuntimeError("Binance Testnet unavailable or API keys invalid")
            logger.info("Connected to Binance Testnet")
            logger.info(f"Current BTC/USDT price: ${price:,.2f}")
            logger.info(f"Available USDT balance: ${balance:,.2f}")

        except Exception as ex:
            logger.warning(f"Binance Testnet not available ({ex}); ")
            sys.exit(1)

        executor = TradeExecutor(exchange)

        # Example: Execute a test signal (replace with actual strategy logic)
        print("\n" + "="*60)
        print("LIVE TRADING TEST")
        print("="*60)
        print("This is a test script. To implement live trading:")
        print("1. Fetch real-time market data from Binance")
        print("2. Calculate indicators (RSI, SMA) on live data")
        print("3. Generate trading signals using your strategy")
        print("4. Execute trades via executor.execute('BUY' or 'SELL')")
        print("="*60)

        # Uncomment to execute a test trade (BE CAREFUL!)
        signal = "BUY"  # or "SELL"
        logger.info(f"Executing test signal: {signal}")
        executor.execute(signal)

        logger.info("Live trading system initialized successfully")

    except Exception as e:
        logger.error(f"Error in live trading system: {e}", exc_info=True)
        sys.exit(1)
