#!/usr/bin/env python3
"""
Live Trading Orchestrator
==========================
This script is a PURE ORCHESTRATOR - it contains NO trading strategy logic.
All strategy decisions are delegated to MultiTFStrategy class.

Responsibilities:
- Wire up exchange + executor
- Delegate live loop to MultiTFStrategy.run_live()

Strategy Logic (handled by MultiTFStrategy):
- Entry/exit conditions
- Stop loss / take profit (ATR-based)
- Live iteration loop, data fetch, and execution
"""
from src.trading.exchange import BinanceExchange
from src.trading.executor import TradeExecutor
from src.strategy.multi_tf import MultiTFStrategy
from config.config import SYMBOL, ENTRY_TIMEFRAME
import logging
import sys

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
    logger.info("="*70)
    logger.info("🚀 LIVE TRADING SYSTEM - Pure Orchestrator")
    logger.info("   All strategy logic delegated to MultiTFStrategy class")
    logger.info("="*70)

    try:
        # Setup exchange connection
        try:
            exchange = BinanceExchange()
            price = exchange.get_current_price()
            auth_ok = getattr(exchange, 'is_authenticated', lambda: False)()
            balance = exchange.get_account_balance("USDT")

            if price is None or not auth_ok:
                raise RuntimeError("Binance Testnet unavailable or API keys invalid")

            logger.info("✅ Connected to Binance Testnet")
            logger.info(f"   Symbol: {SYMBOL}")
            logger.info(f"   Current Price: ${price:,.2f}")
            logger.info(f"   USDT Balance: ${balance:,.2f}")

        except Exception as ex:
            logger.error(f"❌ Binance Testnet connection failed: {ex}")
            logger.error("   Please configure API keys in .env file")
            sys.exit(1)

        # Initialize components (NO strategy logic here!)
        executor = TradeExecutor(exchange, logger=logger)
        strategy = MultiTFStrategy()  # <-- ALL trading logic is in this class

        print("\n" + "="*70)
        print("📊 LIVE TRADING SIMULATION")
        print("="*70)
        print(f"Strategy Class:   MultiTFStrategy (unified for backtest & live)")
        print(f"Parameters:       Fast SMA: {strategy.sma_fast} | Slow SMA: {strategy.sma_slow}")
        print(f"                  RSI Momentum: {strategy.rsi_momentum} | ATR SL: {strategy.atr_sl}x | TP: {strategy.atr_tp}x")
        print(f"Timeframe:        {ENTRY_TIMEFRAME}")
        print(f"Symbol:           {SYMBOL}")
        print()
        print("📝 This script only wires components and hands control to MultiTFStrategy.run_live().")
        print("🎯 ALL TRADING LOGIC + LIVE LOOP are in MultiTFStrategy class")
        print()
        print("Press Ctrl+C to stop trading and view summary")
        print("="*70 + "\n")

        # Use the strategy's built-in live loop (single call)
        strategy.run_live(
            exchange=exchange,
            executor=executor,
            symbol=SYMBOL,
            timeframe=ENTRY_TIMEFRAME,
            fetch_limit=120,
            loop_delay=60,
            max_iterations=None
        )

    except Exception as e:
        logger.error(f"Error in live trading system: {e}", exc_info=True)
        sys.exit(1)