from backtesting import Strategy
import numpy as np

class MultiTFStrategy(Strategy):
    # === Strategy parameters ===
    rsi_period = 14
    sma_fast = 20      # short-term SMA
    sma_slow = 60      # higher timeframe trend
    rsi_momentum = 2   # minimum RSI rise for momentum
    atr_period = 14
    atr_sl = 1.0       # ATR multiplier for SL
    atr_tp = 2.0       # ATR multiplier for TP

    def init(self):
        close = self.data.Close
        high = self.data.High
        low = self.data.Low

        # Fast SMA for entries
        self.sma_fast_line = self.I(
            lambda x: np.convolve(x, np.ones(self.sma_fast)/self.sma_fast, mode='same'), 
            close
        )

        # Slow SMA for trend filter
        self.sma_slow_line = self.I(
            lambda x: np.convolve(x, np.ones(self.sma_slow)/self.sma_slow, mode='same'),
            close
        )

        # RSI
        self.rsi_line = self.I(self._rsi, close, self.rsi_period)

        # ATR
        self.atr_line = self.I(self._atr, high, low, close, self.atr_period)

    def next(self):
        if len(self.data.Close) < self.sma_slow:
            return  # wait until enough data

        close = self.data.Close[-1]
        rsi_now = self.rsi_line[-1]
        rsi_prev = self.rsi_line[-2]
        sma_fast = self.sma_fast_line[-1]
        sma_slow = self.sma_slow_line[-1]
        atr = self.atr_line[-1]

        # Trend direction
        uptrend = sma_fast > sma_slow
        downtrend = sma_fast < sma_slow

        # Momentum check
        rsi_momentum_up = rsi_now - rsi_prev >= self.rsi_momentum
        rsi_momentum_down = rsi_prev - rsi_now >= self.rsi_momentum

        # --- Long Entry ---
        if not self.position and uptrend and rsi_momentum_up:
            self.buy(
                sl=close - self.atr_sl * atr,
                tp=close + self.atr_tp * atr
            )

        # --- Short Entry ---
        if not self.position and downtrend and rsi_momentum_down:
            self.sell(
                sl=close + self.atr_sl * atr,
                tp=close - self.atr_tp * atr
            )

        # --- Exit on strong reversal candle ---
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
                        np.maximum(np.abs(high[1:] - close[:-1]), np.abs(low[1:] - close[:-1])))
        atr = np.convolve(tr, np.ones(period)/period, mode='same')
        return np.concatenate([[tr[0]], atr])
