import logging
from config.config import RISK_PER_TRADE
from src.utils.logger import log_trade_detailed


class TradeExecutor:
    """
    Executes trades on an exchange (live or simulated).
    
    Responsibilities:
    - Calculate position sizes based on risk management rules
    - Place market orders for BUY/SELL signals
    - Validate account balance and order quantities
    - Log all execution attempts (success and failure)
    - Handle edge cases (zero quantities, insufficient balance, etc.)
    
    Attributes:
        exchange: Exchange API wrapper (e.g., BinanceExchange)
        logger: Python logger for debugging and monitoring
    """
    
    def __init__(self, exchange, logger=None):
        """
        Initialize the trade executor.
        
        Args:
            exchange: Exchange wrapper with methods:
                - get_current_price() -> float
                - get_account_balance(asset) -> float
                - place_order(side, qty) -> dict or None
            logger: Optional logger instance. Creates new if not provided.
        """
        self.exchange = exchange
        self.logger = logger or logging.getLogger(__name__)
        self.logger.debug(f"TradeExecutor initialized with exchange: {exchange.__class__.__name__}")

    def execute(self, signal, quantity=None):
        """
        Execute a market order for a given signal.
        
        Implements risk management:
        - BUY: Uses RISK_PER_TRADE % of available USDT
        - SELL: Sells available base asset balance
        
        Args:
            signal: Trading signal - "BUY", "SELL", or "CLOSE"
            quantity: Optional explicit quantity override (float)
                - If provided, validates against available balance
                - Caps at max risk allocation for BUY orders
                - Caps at available holdings for SELL orders
        
        Returns:
            dict: Exchange order response with keys like {
                'orderId': str,
                'executedQty': float,
                'status': str
            } or None if order failed
        
        Raises:
            None (logs errors instead of raising)
        
        Edge cases handled:
        - Invalid signal: logs warning, returns None
        - Missing current price: logs error, returns None
        - Insufficient balance: logs error, returns None
        - Zero quantity after rounding: logs error, returns None
        - Invalid quantity override: logs error, returns None
        """
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
        """
        Execute BUY order with risk management.
        
        Args:
            price: Current market price (float)
            quantity: Optional explicit quantity (float)
        
        Returns:
            Exchange order response or None
        """
        self.logger.debug("_execute_buy() - fetching USDT balance")
        usdt_balance = self.exchange.get_account_balance("USDT")
        
        if usdt_balance <= 0:
            self.logger.error(f"Insufficient USDT balance: {usdt_balance:.2f}")
            return None
        
        self.logger.debug(f"Available USDT balance: {usdt_balance:.2f}")
        
        # If explicit quantity provided, validate and use it
        if quantity is not None:
            return self._execute_buy_explicit(price, quantity, usdt_balance)
        
        # Calculate position size from risk percentage
        return self._execute_buy_risk_based(price, usdt_balance)
    
    def _execute_buy_explicit(self, price, quantity, usdt_balance):
        """
        Execute BUY order with explicit quantity.
        
        Args:
            price: Current price (float)
            quantity: Requested quantity (float)
            usdt_balance: Available USDT (float)
        
        Returns:
            Exchange order response or None
        """
        try:
            qty = float(quantity)
        except Exception as e:
            self.logger.error(f"Invalid quantity provided: {quantity}, error: {e}")
            return None

        if qty <= 0:
            self.logger.error(f"Provided BUY quantity must be > 0, got: {qty}")
            return None

        # Check that provided qty doesn't exceed buying power
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
        """
        Execute BUY order with risk-based position sizing.
        
        Args:
            price: Current price (float)
            usdt_balance: Available USDT (float)
        
        Returns:
            Exchange order response or None
        """
        risk_pct = float(RISK_PER_TRADE)
        usdt_to_use = usdt_balance * risk_pct
        
        self.logger.debug(
            f"Risk-based sizing: balance={usdt_balance:.2f}, "
            f"risk_pct={risk_pct*100:.2f}%, use={usdt_to_use:.2f}"
        )
        
        if usdt_to_use <= 0:
            self.logger.error(
                f"Computed USDT to use is zero: {usdt_to_use:.2f}"
            )
            return None

        qty = usdt_to_use / price
        qty = round(qty, 6)
        
        if qty <= 0:
            self.logger.error(
                f"Computed BUY quantity is zero after rounding: {qty}"
            )
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
        """
        Execute SELL order.
        
        Args:
            price: Current market price (float)
            quantity: Optional explicit quantity (float)
        
        Returns:
            Exchange order response or None
        """
        # Derive base asset from symbol (e.g., BTCUSDT -> BTC)
        base_asset = getattr(self.exchange, "symbol", None)
        if base_asset and base_asset.endswith("USDT"):
            base_asset = base_asset.replace("USDT", "")
        else:
            base_asset = "BTC"
        
        self.logger.debug(f"_execute_sell() - base_asset={base_asset}")
        base_balance = self.exchange.get_account_balance(base_asset)
        
        if base_balance <= 0:
            self.logger.error(
                f"Insufficient {base_asset} balance: {base_balance:.8f}"
            )
            return None
        
        self.logger.debug(f"Available {base_asset} balance: {base_balance:.8f}")
        
        # If explicit quantity provided, validate and use it
        if quantity is not None:
            return self._execute_sell_explicit(price, quantity, base_asset, base_balance)
        
        # Sell all available holdings
        return self._execute_sell_all(price, base_asset, base_balance)
    
    def _execute_sell_explicit(self, price, quantity, base_asset, base_balance):
        """
        Execute SELL order with explicit quantity.
        
        Args:
            price: Current price (float)
            quantity: Requested quantity (float)
            base_asset: Asset being sold (str, e.g., "BTC")
            base_balance: Available holdings (float)
        
        Returns:
            Exchange order response or None
        """
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
        """
        Execute SELL order for all available holdings.
        
        Args:
            price: Current price (float)
            base_asset: Asset being sold (str)
            base_balance: Available holdings (float)
        
        Returns:
            Exchange order response or None
        """
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
