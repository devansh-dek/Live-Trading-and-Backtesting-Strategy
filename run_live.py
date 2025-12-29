#!/usr/bin/env python3
"""
Live trading script for multi-timeframe strategy on Binance Testnet.
WARNING: This will execute real orders on Binance Testnet.
"""

from src.trading.exchange import BinanceExchange
from src.trading.executor import TradeExecutor
from src.strategy.base import BaseStrategy
from src.utils.logger import log_trade
from src.utils.data import to_dataframe
from config.config import SYMBOL, ENTRY_TIMEFRAME
import logging
import sys
import time
import pandas as pd
from datetime import datetime

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


class LiveTradingSession:
    """Manages a live trading session with position tracking and trade summary."""

    def __init__(self, exchange, executor, strategy):
        self.exchange = exchange
        self.executor = executor
        self.strategy = strategy
        self.position = None  # None, "LONG", or "SHORT"
        self.trades = []
        self.entry_price = None
        self.entry_time = None
        self.entry_quantity = None

    def fetch_market_data(self, limit=100):
        """Fetch recent market data from Binance."""
        try:
            klines = self.exchange.client.get_klines(
                symbol=SYMBOL,
                interval=ENTRY_TIMEFRAME,
                limit=limit
            )
            df = to_dataframe(klines, ['timestamp', 'open', 'high', 'low', 'close', 'volume',
                                       'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                                       'taker_buy_quote', 'ignore'])
            return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            return None

    def process_signals(self, df):
        """Process entry and exit signals from strategy."""
        if df is None or len(df) < 50:
            logger.warning("Insufficient data for strategy calculation")
            return

        current_price = self.exchange.get_current_price()
        if current_price is None:
            logger.warning("Cannot fetch current price")
            return

        # Check for exit signal first if we have a position
        if self.position:
            exit_signal = self.strategy.generate_exit_signal(df)

            if (self.position == "LONG" and exit_signal == "CLOSE_LONG") or \
               (self.position == "SHORT" and exit_signal == "CLOSE_SHORT"):
                logger.info(f"EXIT SIGNAL: {exit_signal} at ${current_price:,.2f}")
                self.execute_exit(current_price)
                return

        # Check for entry signal if we don't have a position
        if not self.position:
            entry_signal = self.strategy.generate_entry_signal(df)

            if entry_signal == "BUY":
                logger.info(f"ENTRY SIGNAL: BUY at ${current_price:,.2f}")
                self.execute_entry("BUY", current_price)
            elif entry_signal == "SELL":
                logger.info(f"ENTRY SIGNAL: SELL at ${current_price:,.2f}")
                self.execute_entry("SELL", current_price)

    def execute_entry(self, side, price):
        """Execute entry order and track position."""
        try:
            order = self.executor.execute(side)

            if order:
                self.position = "LONG" if side == "BUY" else "SHORT"
                self.entry_price = price
                self.entry_time = datetime.now()

                # Extract quantity from order response
                self.entry_quantity = float(order.get('executedQty', 0))

                logger.info(f"✓ Entered {self.position} position: {self.entry_quantity} @ ${price:,.2f}")

                # Log to CSV
                log_trade([
                    self.entry_time.isoformat(),
                    side,
                    self.entry_quantity,
                    price,
                    order.get('orderId', 'N/A'),
                    order.get('status', 'FILLED')
                ], "data/live_trades.csv")
            else:
                logger.error(f"Failed to execute {side} order")

        except Exception as e:
            logger.error(f"Error executing entry: {e}")

    def execute_exit(self, price):
        """Execute exit order and record trade."""
        try:
            side = "SELL" if self.position == "LONG" else "BUY"
            order = self.executor.execute(side, self.entry_quantity)

            if order:
                exit_time = datetime.now()
                exit_quantity = float(order.get('executedQty', 0))

                # Calculate PnL
                if self.position == "LONG":
                    pnl = (price - self.entry_price) * self.entry_quantity
                else:  # SHORT
                    pnl = (self.entry_price - price) * self.entry_quantity

                duration = (exit_time - self.entry_time).total_seconds() / 60  # minutes

                trade_record = {
                    'position': self.position,
                    'entry_time': self.entry_time,
                    'exit_time': exit_time,
                    'entry_price': self.entry_price,
                    'exit_price': price,
                    'quantity': self.entry_quantity,
                    'pnl': pnl,
                    'duration_min': duration
                }
                self.trades.append(trade_record)

                logger.info(f"✓ Exited {self.position} position: {exit_quantity} @ ${price:,.2f} | PnL: ${pnl:,.2f}")

                # Log to CSV
                log_trade([
                    exit_time.isoformat(),
                    side,
                    exit_quantity,
                    price,
                    order.get('orderId', 'N/A'),
                    order.get('status', 'FILLED')
                ], "data/live_trades.csv")

                # Reset position
                self.position = None
                self.entry_price = None
                self.entry_time = None
                self.entry_quantity = None
            else:
                logger.error(f"Failed to execute exit order")

        except Exception as e:
            logger.error(f"Error executing exit: {e}")

    def print_summary(self):
        """Print trading session summary."""
        print("\n" + "="*70)
        print("LIVE TRADING SESSION SUMMARY")
        print("="*70)

        if not self.trades:
            print("No completed trades in this session.")
            print("="*70)
            return

        total_trades = len(self.trades)
        winning_trades = sum(1 for t in self.trades if t['pnl'] > 0)
        losing_trades = sum(1 for t in self.trades if t['pnl'] <= 0)
        total_pnl = sum(t['pnl'] for t in self.trades)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        print(f"Total Trades:          {total_trades}")
        print(f"Winning Trades:        {winning_trades}")
        print(f"Losing Trades:         {losing_trades}")
        print(f"Win Rate:              {win_rate:.2f}%")
        print(f"Total PnL:             ${total_pnl:,.2f}")
        print(f"Average PnL/Trade:     ${total_pnl/total_trades:,.2f}")
        print()
        print("Trade Details:")
        print("-" * 70)

        for i, trade in enumerate(self.trades, 1):
            print(f"Trade #{i} ({trade['position']})")
            print(f"  Entry:  {trade['entry_time'].strftime('%Y-%m-%d %H:%M:%S')} @ ${trade['entry_price']:,.2f}")
            print(f"  Exit:   {trade['exit_time'].strftime('%Y-%m-%d %H:%M:%S')} @ ${trade['exit_price']:,.2f}")
            print(f"  PnL:    ${trade['pnl']:,.2f} | Duration: {trade['duration_min']:.1f} min")
            print()

        print("="*70)


if __name__ == "__main__":
    logger.info("="*60)
    logger.info("Starting Live Trading System")
    logger.info("="*60)

    try:
        # Initialize exchange and executor
        try:
            exchange = BinanceExchange()
            price = exchange.get_current_price()
            auth_ok = getattr(exchange, 'is_authenticated', lambda: False)()
            balance = exchange.get_account_balance("USDT")

            if price is None or not auth_ok:
                raise RuntimeError("Binance Testnet unavailable or API keys invalid")

            logger.info("✓ Connected to Binance Testnet")
            logger.info(f"  Symbol: {SYMBOL}")
            logger.info(f"  Current Price: ${price:,.2f}")
            logger.info(f"  USDT Balance: ${balance:,.2f}")

        except Exception as ex:
            logger.error(f"Binance Testnet connection failed: {ex}")
            logger.error("Please configure API keys in .env file")
            sys.exit(1)

        executor = TradeExecutor(exchange, logger=logger)
        strategy = BaseStrategy()
        session = LiveTradingSession(exchange, executor, strategy)

        print("\n" + "="*60)
        print("LIVE TRADING SIMULATION")
        print("="*60)
        print(f"Strategy: Multi-Timeframe RSI + SMA")
        print(f"Timeframe: {ENTRY_TIMEFRAME} (confirmation every 4 bars)")
        print(f"Symbol: {SYMBOL}")
        print()
        print("Press Ctrl+C to stop trading and view summary")
        print("="*60 + "\n")

        # Main trading loop
        iteration = 0
        try:
            while True:
                iteration += 1
                logger.info(f"--- Iteration {iteration} ---")

                # Fetch market data
                df = session.fetch_market_data(limit=100)

                if df is not None:
                    # Process signals and execute trades
                    session.process_signals(df)

                    # Display current status
                    current_price = exchange.get_current_price()
                    logger.info(f"Current Price: ${current_price:,.2f} | Position: {session.position or 'NONE'}")

                # Wait before next iteration (e.g., check every minute)
                logger.info("Waiting 60 seconds before next check...\n")
                time.sleep(3)

        except KeyboardInterrupt:
            logger.info("\n\nReceived stop signal. Closing session...")

            # If still in position, close it
            if session.position:
                logger.info(f"Closing open {session.position} position...")
                current_price = exchange.get_current_price()
                session.execute_exit(current_price)

            # Print summary
            session.print_summary()

            logger.info("Live trading session ended.")

    except Exception as e:
        logger.error(f"Error in live trading system: {e}", exc_info=True)
        sys.exit(1)
