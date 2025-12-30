from backtesting import Strategy
import numpy as np

class MultiTFStrategy(Strategy):
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