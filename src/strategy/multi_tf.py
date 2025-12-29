from backtesting import Strategy
import numpy as np
import pandas as pd


class MultiTFStrategy(Strategy):
    rsi_period = 14
    sma_period = 50
    confirm_interval = 4  # number of bars on entry timeframe per confirmation timeframe (15m -> 1h)

    # Entry/exit thresholds (tweakable)
    rsi_long_entry = 40
    rsi_short_entry = 60
    rsi_long_exit = 70
    rsi_short_exit = 30
    sma_break_pct = 0.005  # 0.5%

    def init(self):
        close = self.data.Close

        def rsi_calc(arr, period):
            s = pd.Series(np.asarray(arr, dtype=float))
            delta = s.diff()
            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)
            avg_gain = gain.ewm(alpha=1/period, min_periods=period).mean()
            avg_loss = loss.ewm(alpha=1/period, min_periods=period).mean()
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.values

        def sma_calc(arr, period):
            s = pd.Series(np.asarray(arr, dtype=float))
            return s.rolling(period).mean().values

        # Compute indicators on the strategy timeframe using array-safe functions
        self.rsi = self.I(lambda s: rsi_calc(s, self.rsi_period), close)
        self.sma50 = self.I(lambda s: sma_calc(s, self.sma_period), close)

        # bar counter to simulate confirmation timeframe (every `confirm_interval` bars)
        self._bar_count = 0

    def next(self):
        # increment bar counter
        self._bar_count += 1

        price = float(self.data.Close[-1])
        rsi = float(self.rsi[-1]) if not np.isnan(self.rsi[-1]) else None
        sma = float(self.sma50[-1]) if not np.isnan(self.sma50[-1]) else None

        # If indicators are not ready, skip
        if rsi is None or sma is None:
            return

        # Determine if this bar is a confirmation bar (simulates higher timeframe)
        is_confirmation_bar = (self._bar_count % self.confirm_interval) == 0

        # ENTRY logic (only on confirmation bars)
        if not self.position:
            if is_confirmation_bar:
                # Long entry: RSI below long threshold (oversold) and price above SMA
                if rsi < self.rsi_long_entry and price > sma:
                    self.buy()
                    return

                # Short entry: RSI above short threshold (overbought) and price below SMA
                if rsi > self.rsi_short_entry and price < sma:
                    self.sell()
                    return

            # not confirmation bar or no entry conditions met -> do nothing
            return

        # EXIT logic while in position
        if self.position.is_long:
            # Exit if RSI indicates overbought OR price drops below SMA by threshold
            if rsi > self.rsi_long_exit:
                self.position.close()
                return

            if price < (sma * (1 - self.sma_break_pct)):
                self.position.close()
                return

        elif self.position.is_short:
            # Exit if RSI indicates oversold OR price rises above SMA by threshold
            if rsi < self.rsi_short_exit:
                self.position.close()
                return

            if price > (sma * (1 + self.sma_break_pct)):
                self.position.close()
                return

        # No other action; let position run
