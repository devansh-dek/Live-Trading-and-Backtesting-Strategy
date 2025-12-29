import logging
from config.config import RISK_PER_TRADE


class TradeExecutor:
    def __init__(self, exchange, logger=None):
        self.exchange = exchange
        self.logger = logger or logging.getLogger(__name__)

    def execute(self, signal, quantity=None):
        """Execute a market order for a given `signal` ("BUY" or "SELL").

        BUY: compute quantity from available USDT using `RISK_PER_TRADE`.
        SELL: sell available base asset balance (e.g., BTC).

        Returns the exchange order response or None on failure.
        """
        signal = (signal or "").upper()

        price = self.exchange.get_current_price()
        if price is None:
            self.logger.error("Cannot fetch current price; aborting order")
            return None

        if signal == "BUY":
            usdt_balance = self.exchange.get_account_balance("USDT")
            if usdt_balance <= 0:
                self.logger.error("Insufficient USDT balance to place BUY order")
                return None
            # If explicit quantity provided, validate and use it
            if quantity is not None:
                try:
                    qty = float(quantity)
                except Exception:
                    self.logger.error("Provided quantity is invalid")
                    return None

                if qty <= 0:
                    self.logger.error("Provided BUY quantity must be > 0")
                    return None

                # check that provided qty doesn't exceed buying power
                max_qty = (usdt_balance * float(RISK_PER_TRADE)) / price
                if qty > max_qty:
                    self.logger.warning("Provided BUY quantity exceeds risk allocation; capping to max allowed")
                    qty = max_qty

                qty = round(qty, 6)
                if qty <= 0:
                    self.logger.error("Computed BUY quantity is zero after rounding")
                    return None

                usdt_used = qty * price
                self.logger.info(f"Placing BUY order (explicit): qty={qty} (~{usdt_used:.2f} USDT at {price})")
                return self.exchange.place_order("BUY", qty)

            usdt_to_use = usdt_balance * float(RISK_PER_TRADE)
            if usdt_to_use <= 0:
                self.logger.error("Computed USDT to use is zero; check RISK_PER_TRADE")
                return None

            qty = usdt_to_use / price
            qty = round(qty, 6)
            if qty <= 0:
                self.logger.error("Computed BUY quantity is zero after rounding")
                return None

            self.logger.info(f"Placing BUY order: qty={qty} (~{usdt_to_use:.2f} USDT at {price})")
            return self.exchange.place_order("BUY", qty)

        elif signal == "SELL":
            # derive base asset from symbol if possible (e.g. BTCUSDT -> BTC)
            base_asset = getattr(self.exchange, "symbol", None)
            if base_asset and base_asset.endswith("USDT"):
                base_asset = base_asset.replace("USDT", "")
            else:
                base_asset = "BTC"

            base_balance = self.exchange.get_account_balance(base_asset)
            if base_balance <= 0:
                self.logger.error(f"Insufficient {base_asset} balance to place SELL order")
                return None
            # If explicit quantity provided, validate and cap at available balance
            if quantity is not None:
                try:
                    qty = float(quantity)
                except Exception:
                    self.logger.error("Provided quantity is invalid")
                    return None

                if qty <= 0:
                    self.logger.error("Provided SELL quantity must be > 0")
                    return None

                if qty > base_balance:
                    self.logger.warning("Provided SELL quantity exceeds available balance; capping to available")
                    qty = base_balance

                qty = round(qty, 6)
                if qty <= 0:
                    self.logger.error("Computed SELL quantity is zero after rounding")
                    return None

                self.logger.info(f"Placing SELL order (explicit): qty={qty} {base_asset}")
                return self.exchange.place_order("SELL", qty)

            qty = round(base_balance, 6)
            self.logger.info(f"Placing SELL order: qty={qty} {base_asset}")
            return self.exchange.place_order("SELL", qty)

        else:
            self.logger.warning(f"Unknown signal received: {signal}")
            return None
