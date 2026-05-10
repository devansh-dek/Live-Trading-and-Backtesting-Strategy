import logging
from config.config import RISK_PER_TRADE


class TradeExecutor:
    def __init__(self, exchange, logger=None):
        self.exchange = exchange
        self.logger = logger or logging.getLogger(__name__)
        self.logger.debug(f"TradeExecutor initialized with {exchange.__class__.__name__}")

    def execute(self, signal, quantity=None):
        """Execute market order based on signal (BUY/SELL)"""
        signal = (signal or "").upper()
        self.logger.debug(f"execute() called with signal={signal}, quantity={quantity}")

        price = self.exchange.get_current_price()
        if price is None:
            self.logger.error("Cannot fetch current price; aborting order")
            return None

        if signal == "BUY":
            return self._execute_buy(price, quantity)
        elif signal == "SELL":
            return self._execute_sell(price, quantity)
        else:
            self.logger.warning(f"Unknown signal received: {signal}")
            return None

    def _execute_buy(self, price, quantity=None):
        self.logger.debug("_execute_buy() - fetching USDT balance")
        usdt_balance = self.exchange.get_account_balance("USDT")

        if usdt_balance <= 0:
            self.logger.error(f"Insufficient USDT balance: {usdt_balance:.2f}")
            return None

        self.logger.debug(f"Available USDT balance: {usdt_balance:.2f}")

        if quantity is not None:
            return self._execute_buy_explicit(price, quantity, usdt_balance)

        return self._execute_buy_risk_based(price, usdt_balance)

    def _execute_buy_explicit(self, price, quantity, usdt_balance):
        try:
            qty = float(quantity)
        except Exception as e:
            self.logger.error(f"Invalid quantity provided: {quantity}, error: {e}")
            return None

        if qty <= 0:
            self.logger.error(f"Provided BUY quantity must be > 0, got: {qty}")
            return None

        # cap at max risk allocation
        max_qty = (usdt_balance * float(RISK_PER_TRADE)) / price
        if qty > max_qty:
            self.logger.warning(
                f"Requested qty {qty:.6f} exceeds max allowed {max_qty:.6f}; capping"
            )
            qty = max_qty

        qty = round(qty, 6)
        if qty <= 0:
            self.logger.error(f"Computed BUY quantity is zero after rounding: {qty}")
            return None

        usdt_used = qty * price
        self.logger.info(
            f"Placing BUY order (explicit): qty={qty:.6f} @ ${price:,.2f} "
            f"(${usdt_used:,.2f} USDT)"
        )

        order = self.exchange.place_order("BUY", qty)
        if order:
            self.logger.info(f"✓ BUY order executed: {order.get('orderId', 'N/A')}")
        else:
            self.logger.error("✗ BUY order failed")

        return order

    def _execute_buy_risk_based(self, price, usdt_balance):
        risk_pct = float(RISK_PER_TRADE)
        usdt_to_use = usdt_balance * risk_pct

        self.logger.debug(
            f"Risk-based sizing: balance={usdt_balance:.2f}, "
            f"risk_pct={risk_pct*100:.2f}%, use={usdt_to_use:.2f}"
        )

        if usdt_to_use <= 0:
            self.logger.error(f"Computed USDT to use is zero: {usdt_to_use:.2f}")
            return None

        qty = usdt_to_use / price
        qty = round(qty, 6)

        if qty <= 0:
            self.logger.error(f"Computed BUY quantity is zero after rounding: {qty}")
            return None

        self.logger.info(
            f"Placing BUY order: qty={qty:.6f} @ ${price:,.2f} "
            f"(${usdt_to_use:,.2f} USDT, {risk_pct*100:.2f}% risk)"
        )

        order = self.exchange.place_order("BUY", qty)
        if order:
            self.logger.info(f"✓ BUY order executed: {order.get('orderId', 'N/A')}")
        else:
            self.logger.error("✗ BUY order failed")

        return order

    def _execute_sell(self, price, quantity=None):
        # derive base asset from symbol (BTCUSDT -> BTC)
        base_asset = getattr(self.exchange, "symbol", None)
        if base_asset and base_asset.endswith("USDT"):
            base_asset = base_asset.replace("USDT", "")
        else:
            base_asset = "BTC"

        self.logger.debug(f"_execute_sell() - base_asset={base_asset}")
        base_balance = self.exchange.get_account_balance(base_asset)

        if base_balance <= 0:
            self.logger.error(f"Insufficient {base_asset} balance: {base_balance:.8f}")
            return None

        self.logger.debug(f"Available {base_asset} balance: {base_balance:.8f}")

        if quantity is not None:
            return self._execute_sell_explicit(price, quantity, base_asset, base_balance)

        return self._execute_sell_all(price, base_asset, base_balance)

    def _execute_sell_explicit(self, price, quantity, base_asset, base_balance):
        try:
            qty = float(quantity)
        except Exception as e:
            self.logger.error(f"Invalid quantity provided: {quantity}, error: {e}")
            return None

        if qty <= 0:
            self.logger.error(f"Provided SELL quantity must be > 0, got: {qty}")
            return None

        if qty > base_balance:
            self.logger.warning(
                f"Requested qty {qty:.8f} exceeds available {base_balance:.8f}; capping"
            )
            qty = base_balance

        qty = round(qty, 6)
        if qty <= 0:
            self.logger.error(f"Computed SELL quantity is zero after rounding: {qty}")
            return None

        usdt_value = qty * price
        self.logger.info(
            f"Placing SELL order (explicit): qty={qty:.6f} {base_asset} "
            f"@ ${price:,.2f} (${usdt_value:,.2f} USDT)"
        )

        order = self.exchange.place_order("SELL", qty)
        if order:
            self.logger.info(f"✓ SELL order executed: {order.get('orderId', 'N/A')}")
        else:
            self.logger.error("✗ SELL order failed")

        return order

    def _execute_sell_all(self, price, base_asset, base_balance):
        qty = round(base_balance, 6)
        usdt_value = qty * price

        self.logger.info(
            f"Placing SELL order (full position): qty={qty:.6f} {base_asset} "
            f"@ ${price:,.2f} (${usdt_value:,.2f} USDT)"
        )

        order = self.exchange.place_order("SELL", qty)
        if order:
            self.logger.info(f"✓ SELL order executed: {order.get('orderId', 'N/A')}")
        else:
            self.logger.error("✗ SELL order failed")

        return order