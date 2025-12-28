from backtesting import Strategy
import numpy as np
import pandas as pd


class MultiTFStrategy(Strategy):
    rsi_period = 14
    sma_period = 50

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

    def next(self):
        price = float(self.data.Close[-1])
        rsi = float(self.rsi[-1])
        sma = float(self.sma50[-1])

        # Entry logic
        if not self.position:
            if rsi < 30 and price > sma:
                self.buy()
            elif rsi > 70 and price < sma:
                self.sell()
            return

        # Exit logic — simple rules to close positions
        if self.position.is_long:
            if rsi > 60 or price < sma:
                self.position.close()
        elif self.position.is_short:
            if rsi < 40 or price > sma:
                self.position.close()
