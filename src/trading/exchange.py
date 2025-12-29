from binance.client import Client
from binance.enums import *
from config.config import API_KEY, API_SECRET, SYMBOL
import logging
import pandas as pd
import os

logger = logging.getLogger(__name__)

class BinanceExchange:
    """Wrapper for Binance Testnet API operations."""

    def __init__(self):
        # Initialize client; if keys are empty this may still create a client but calls will fail
        try:
            self.client = Client(API_KEY, API_SECRET, testnet=True)
        except Exception:
            # Leave client unset; caller should handle errors
            self.client = None
        self.symbol = SYMBOL
        logger.info(f"Initialized BinanceExchange for {self.symbol} on Testnet")

    def get_account_balance(self, asset="USDT"):
        """Get available balance for a specific asset."""
        try:
            account = self.client.get_account()
            for balance in account['balances']:
                if balance['asset'] == asset:
                    return float(balance['free'])
            return 0.0
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return 0.0

    def place_order(self, side, quantity):
        """
        Place a market order on Binance Testnet.

        Args:
            side: "BUY" or "SELL"
            quantity: Amount to trade (in base asset, e.g., BTC)

        Returns:
            Order response dict or None on failure
        """
        try:
            order = self.client.create_order(
                symbol=self.symbol,
                side=side,
                type=ORDER_TYPE_MARKET,
                quantity=quantity
            )
            logger.info(f"Order placed: {side} {quantity} {self.symbol}")
            logger.info(f"Order ID: {order['orderId']}")
            return order
        except Exception as e:
            logger.error(f"Error placing {side} order: {e}")
            return None

    def get_current_price(self):
        """Get current market price for the symbol."""
        try:
            if not self.client:
                raise RuntimeError("Binance client not initialized")
            ticker = self.client.get_symbol_ticker(symbol=self.symbol)
            return float(ticker['price'])
        except Exception as e:
            logger.error(f"Error fetching price: {e}")
            return None

    def is_authenticated(self):
        """Return True if API key/secret appear valid (account endpoint accessible)."""
        try:
            if not self.client:
                return False
            self.client.get_account()
            return True
        except Exception:
            return False

