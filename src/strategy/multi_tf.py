from backtesting import Strategy
import numpy as np
import pandas as pd
import logging
import time
from datetime import datetime

class MultiTFStrategy(Strategy):
    """
    Unified Multi-Timeframe Strategy for both Backtesting and Live Trading.

    Usage:
    ------
    # For Backtesting (with backtesting.py library):
    bt = Backtest(df, MultiTFStrategy, cash=100_000, commission=0.002)
    results = bt.run()

    # For Live Trading (signal generation):
    strategy = MultiTFStrategy()
    signal = strategy.generate_entry_signal(df)  # Returns "BUY", "SELL", or None
    exit_signal = strategy.generate_exit_signal(df, position="LONG")  # Returns "CLOSE_LONG", "CLOSE_SHORT", or None
    """

    # params
    rsi_period = 14
    sma_fast = 20
    sma_slow = 60
    rsi_momentum = 2  # min RSI rise for momentum signal
    atr_period = 14
    atr_sl = 1.0  # stop loss multiplier
    atr_tp = 2.0  # take profit multiplier

    def init(self):
        close = self.data.Close
        high = self.data.High
        low = self.data.Low

        # SMAs for trend
        self.sma_fast_line = self.I(
            lambda x: np.convolve(x, np.ones(self.sma_fast)/self.sma_fast, mode='same'),
            close
        )
        self.sma_slow_line = self.I(
            lambda x: np.convolve(x, np.ones(self.sma_slow)/self.sma_slow, mode='same'),
            close
        )

        # RSI and ATR
        self.rsi_line = self.I(self._rsi, close, self.rsi_period)
        self.atr_line = self.I(self._atr, high, low, close, self.atr_period)

    def next(self):
        if len(self.data.Close) < self.sma_slow:
            return

        close = self.data.Close[-1]
        rsi_now = self.rsi_line[-1]
        rsi_prev = self.rsi_line[-2]
        sma_fast = self.sma_fast_line[-1]
        sma_slow = self.sma_slow_line[-1]
        atr = self.atr_line[-1]

        uptrend = sma_fast > sma_slow
        downtrend = sma_fast < sma_slow

        rsi_momentum_up = rsi_now - rsi_prev >= self.rsi_momentum
        rsi_momentum_down = rsi_prev - rsi_now >= self.rsi_momentum

        # long entry
        if not self.position and uptrend and rsi_momentum_up:
            self.buy(
                sl=close - self.atr_sl * atr,
                tp=close + self.atr_tp * atr
            )

        # short entry
        if not self.position and downtrend and rsi_momentum_down:
            self.sell(
                sl=close + self.atr_sl * atr,
                tp=close - self.atr_tp * atr
            )

        # exit on reversal
        if self.position.is_long and close < sma_fast:
            self.position.close()
        if self.position.is_short and close > sma_fast:
            self.position.close()

    @staticmethod
    def _rsi(series, period):
        delta = np.diff(series)
        up = np.where(delta > 0, delta, 0)
        down = np.where(delta < 0, -delta, 0)

        roll_up = np.convolve(up, np.ones(period)/period, mode='same')
        roll_down = np.convolve(down, np.ones(period)/period, mode='same')

        rs = roll_up / (roll_down + 1e-9)
        rsi = 100 - (100 / (1 + rs))
        return np.concatenate([[50], rsi])

    @staticmethod
    def _atr(high, low, close, period):
        tr = np.maximum(high[1:] - low[1:],
                        np.maximum(np.abs(high[1:] - close[:-1]),
                                   np.abs(low[1:] - close[:-1])))
        atr = np.convolve(tr, np.ones(period)/period, mode='same')
        return np.concatenate([[tr[0]], atr])

    # ========================================================================
    # LIVE TRADING METHODS - Signal Generation from DataFrames
    # ========================================================================

    def _calculate_indicators(self, df):
        """
        Calculate all indicators from a raw OHLCV dataframe.
        Used for live trading signal generation.

        Parameters:
        -----------
        df : pandas.DataFrame
            OHLCV data with columns: open, high, low, close, volume

        Returns:
        --------
        dict
            Dictionary containing calculated indicator values
        """
        # Normalize column names
        df = df.copy()
        df.columns = [c.lower() for c in df.columns]

        if len(df) < self.sma_slow:
            return None

        close = df['close'].values
        high = df['high'].values
        low = df['low'].values

        # Calculate SMAs
        sma_fast = np.convolve(close, np.ones(self.sma_fast)/self.sma_fast, mode='same')
        sma_slow = np.convolve(close, np.ones(self.sma_slow)/self.sma_slow, mode='same')

        # Calculate RSI
        rsi = self._rsi(close, self.rsi_period)

        # Calculate ATR
        atr = self._atr(high, low, close, self.atr_period)

        return {
            'close': close[-1],
            'sma_fast': sma_fast[-1],
            'sma_slow': sma_slow[-1],
            'rsi_now': rsi[-1],
            'rsi_prev': rsi[-2] if len(rsi) > 1 else rsi[-1],
            'atr': atr[-1]
        }

    def generate_entry_signal(self, df):
        """
        Generate entry signals for live trading.

        Parameters:
        -----------
        df : pandas.DataFrame
            OHLCV dataframe with at least sma_slow bars

        Returns:
        --------
        str or None
            "BUY" - Enter long position
            "SELL" - Enter short position
            None - No signal
        """
        indicators = self._calculate_indicators(df)

        if indicators is None:
            return None

        close = indicators['close']
        sma_fast = indicators['sma_fast']
        sma_slow = indicators['sma_slow']
        rsi_now = indicators['rsi_now']
        rsi_prev = indicators['rsi_prev']

        # Check if data is valid
        if np.isnan([close, sma_fast, sma_slow, rsi_now, rsi_prev]).any():
            return None

        # Determine trend
        uptrend = sma_fast > sma_slow
        downtrend = sma_fast < sma_slow

        # Calculate RSI momentum
        rsi_momentum_up = rsi_now - rsi_prev >= self.rsi_momentum
        rsi_momentum_down = rsi_prev - rsi_now >= self.rsi_momentum

        # Entry logic (same as next() method)
        if uptrend and rsi_momentum_up:
            return "BUY"
        elif downtrend and rsi_momentum_down:
            return "SELL"

        return None

    def generate_exit_signal(self, df, position=None):
        """
        Generate exit signals for live trading.

        Parameters:
        -----------
        df : pandas.DataFrame
            OHLCV dataframe
        position : str
            Current position: "LONG" or "SHORT"

        Returns:
        --------
        str or None
            "CLOSE_LONG" - Exit long position
            "CLOSE_SHORT" - Exit short position
            None - No exit signal
        """
        if position is None:
            return None

        indicators = self._calculate_indicators(df)

        if indicators is None:
            return None

        close = indicators['close']
        sma_fast = indicators['sma_fast']

        if np.isnan([close, sma_fast]).any():
            return None

        # Exit logic (same as next() method)
        if position == "LONG" and close < sma_fast:
            return "CLOSE_LONG"
        elif position == "SHORT" and close > sma_fast:
            return "CLOSE_SHORT"

        return None

    def get_stop_loss(self, df, entry_price, side):
        """
        Calculate stop loss price based on ATR.

        Parameters:
        -----------
        df : pandas.DataFrame
            OHLCV dataframe
        entry_price : float
            Entry price of the position
        side : str
            "BUY" for long, "SELL" for short

        Returns:
        --------
        float
            Stop loss price
        """
        indicators = self._calculate_indicators(df)
        if indicators is None:
            # Fallback to 2% stop loss
            return entry_price * 0.98 if side == "BUY" else entry_price * 1.02

        atr = indicators['atr']

        if side == "BUY":
            return entry_price - (self.atr_sl * atr)
        else:
            return entry_price + (self.atr_sl * atr)

    def get_take_profit(self, df, entry_price, side):
        """
        Calculate take profit price based on ATR.

        Parameters:
        -----------
        df : pandas.DataFrame
            OHLCV dataframe
        entry_price : float
            Entry price of the position
        side : str
            "BUY" for long, "SELL" for short

        Returns:
        --------
        float
            Take profit price
        """
        indicators = self._calculate_indicators(df)
        if indicators is None:
            # Fallback to 4% take profit
            return entry_price * 1.04 if side == "BUY" else entry_price * 0.96

        atr = indicators['atr']

        if side == "BUY":
            return entry_price + (self.atr_tp * atr)
        else:
            return entry_price - (self.atr_tp * atr)

    # ========================================================================
    # ONE-CALL LIVE TRADING LOOP (ORCHESTRATOR INSIDE THE STRATEGY)
    # ========================================================================

    def run_live(self, exchange=None, executor=None, symbol=None, timeframe=None,
                 fetch_limit=120, loop_delay=60, max_iterations=None):
        """
        Run a live trading loop using this strategy's logic.

        Parameters
        ----------
        exchange : BinanceExchange, optional
            Reuse an existing exchange instance. If None, a new one is created.
        executor : TradeExecutor, optional
            Reuse an existing executor. If None, a new one is created.
        symbol : str, optional
            Trading symbol; defaults to config.config.SYMBOL.
        timeframe : str, optional
            Kline interval; defaults to config.config.ENTRY_TIMEFRAME.
        fetch_limit : int, default 120
            Number of candles to fetch each loop (must be >= sma_slow).
        loop_delay : int, default 60
            Seconds to sleep between iterations.
        max_iterations : int, optional
            Stop after N iterations (None = run indefinitely).
        """

        # Lazy imports to avoid forcing dependencies during backtests
        if symbol is None or timeframe is None:
            try:
                from config.config import SYMBOL as DEFAULT_SYMBOL, ENTRY_TIMEFRAME as DEFAULT_TIMEFRAME
            except Exception as exc:  # pragma: no cover - defensive
                raise RuntimeError("Failed to load default symbol/timeframe from config") from exc
            symbol = symbol or DEFAULT_SYMBOL
            timeframe = timeframe or DEFAULT_TIMEFRAME

        if exchange is None:
            from src.trading.exchange import BinanceExchange
            exchange = BinanceExchange()

        if executor is None:
            from src.trading.executor import TradeExecutor
            executor = TradeExecutor(exchange, logger=logging.getLogger(__name__))

        from src.utils.data import to_dataframe

        logger = logging.getLogger(__name__)

        # Validate connection
        price = exchange.get_current_price()
        auth_ok = getattr(exchange, "is_authenticated", lambda: False)()
        balance = exchange.get_account_balance("USDT")
        if price is None or not auth_ok:
            raise RuntimeError("Exchange unavailable or API keys invalid")

        logger.info("=" * 70)
        logger.info("Starting live trading via MultiTFStrategy.run_live()")
        logger.info(f"Symbol: {symbol} | Timeframe: {timeframe} | Starting Price: ${price:,.2f}")
        logger.info(f"USDT Balance: ${balance:,.2f}")
        logger.info("All trading logic is handled by MultiTFStrategy methods.")
        logger.info("=" * 70)

        position = None
        entry_price = None
        entry_time = None
        entry_quantity = None
        trades = []

        iteration = 0
        try:
            while True:
                iteration += 1
                if max_iterations is not None and iteration > max_iterations:
                    logger.info("Max iterations reached; stopping live loop.")
                    break

                logger.info(f"--- Live Iteration {iteration} ---")

                # Fetch market data
                try:
                    klines = exchange.client.get_klines(symbol=symbol, interval=timeframe, limit=fetch_limit)
                    df = to_dataframe(
                        klines,
                        ['timestamp', 'open', 'high', 'low', 'close', 'volume',
                         'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                         'taker_buy_quote', 'ignore']
                    )
                    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
                except Exception as exc:
                    logger.error(f"Error fetching market data: {exc}")
                    time.sleep(loop_delay)
                    continue

                if df is None or len(df) < self.sma_slow:
                    logger.warning(f"Insufficient data (need {self.sma_slow} bars)")
                    time.sleep(loop_delay)
                    continue

                current_price = exchange.get_current_price()
                if current_price is None:
                    logger.warning("Cannot fetch current price")
                    time.sleep(loop_delay)
                    continue

                # Exit logic
                if position:
                    exit_signal = self.generate_exit_signal(df, position=position)
                    if exit_signal:
                        logger.info(f"EXIT SIGNAL: {exit_signal} @ ${current_price:,.2f}")
                        try:
                            side = "SELL" if position == "LONG" else "BUY"
                            order = executor.execute(side, entry_quantity)
                            if order:
                                exit_time = datetime.now()
                                exit_qty = float(order.get('executedQty', 0))
                                pnl = (current_price - entry_price) * entry_quantity if position == "LONG" else (entry_price - current_price) * entry_quantity
                                duration = (exit_time - entry_time).total_seconds() / 60
                                trades.append({
                                    'position': position,
                                    'entry_time': entry_time,
                                    'exit_time': exit_time,
                                    'entry_price': entry_price,
                                    'exit_price': current_price,
                                    'quantity': entry_quantity,
                                    'pnl': pnl,
                                    'duration_min': duration
                                })
                                logger.info(f"Closed {position} | Qty: {exit_qty} | PnL: ${pnl:,.2f}")
                                position = None
                                entry_price = None
                                entry_time = None
                                entry_quantity = None
                            else:
                                logger.error("Failed to execute exit order")
                        except Exception as exc:
                            logger.error(f"Error during exit: {exc}")
                        time.sleep(loop_delay)
                        continue

                # Entry logic
                if not position:
                    entry_signal = self.generate_entry_signal(df)
                    if entry_signal in ("BUY", "SELL"):
                        logger.info(f"ENTRY SIGNAL: {entry_signal} @ ${current_price:,.2f}")
                        try:
                            order = executor.execute(entry_signal)
                            if order:
                                position = "LONG" if entry_signal == "BUY" else "SHORT"
                                entry_price = current_price
                                entry_time = datetime.now()
                                entry_quantity = float(order.get('executedQty', 0))

                                stop_loss = self.get_stop_loss(df, entry_price, entry_signal)
                                take_profit = self.get_take_profit(df, entry_price, entry_signal)
                                logger.info(
                                    f"Entered {position} | Qty: {entry_quantity} | SL: ${stop_loss:,.2f} | TP: ${take_profit:,.2f}"
                                )
                            else:
                                logger.error("Failed to execute entry order")
                        except Exception as exc:
                            logger.error(f"Error during entry: {exc}")

                logger.info(f"Loop complete | Price: ${current_price:,.2f} | Position: {position or 'FLAT'}")
                time.sleep(loop_delay)

        except KeyboardInterrupt:
            logger.info("Received stop signal; exiting live loop...")
            if position:
                try:
                    side = "SELL" if position == "LONG" else "BUY"
                    order = executor.execute(side, entry_quantity)
                    if order:
                        logger.info(f"Closed open {position} position on shutdown.")
                except Exception as exc:
                    logger.error(f"Error closing position on shutdown: {exc}")

        # Print session summary
        if trades:
            total_pnl = sum(t['pnl'] for t in trades)
            wins = sum(1 for t in trades if t['pnl'] > 0)
            win_rate = (wins / len(trades) * 100) if trades else 0
            logger.info("=" * 70)
            logger.info("LIVE TRADING SESSION SUMMARY")
            logger.info(f"Trades: {len(trades)} | Win Rate: {win_rate:.2f}% | PnL: ${total_pnl:,.2f}")
            logger.info("=" * 70)
        else:
            logger.info("No completed trades in session.")