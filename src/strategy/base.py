import numpy as np
import pandas as pd


class BaseStrategy:
    """
    Base strategy for live/paper trading with 15m data + 1h confirmation.
    Returns simple signals: "BUY", "SELL", "CLOSE_LONG", "CLOSE_SHORT", or None
    """

    rsi_period = 14
    sma_period = 50
    confirm_interval = 4  # every 4 bars = 1h on 15m

    rsi_long_entry = 40
    rsi_short_entry = 60
    rsi_long_exit = 70
    rsi_short_exit = 30
    sma_break_pct = 0.005

    def _normalize_cols(self, df):
        if df is None or len(df) == 0:
            return df
        
        cols = {c: c.lower() for c in df.columns}
        df = df.rename(columns=cols)
        
        # make sure we have standard names
        rename = {}
        for col in ["open", "high", "low", "close", "volume"]:
            if col in df.columns:
                rename[col] = col
        
        return df.rename(columns=rename)

    def _calc_rsi(self, close, period):
        s = pd.Series(np.asarray(close, dtype=float))
        delta = s.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        
        avg_gain = gain.ewm(alpha=1/period, min_periods=period).mean()
        avg_loss = loss.ewm(alpha=1/period, min_periods=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calc_sma(self, close, period):
        s = pd.Series(np.asarray(close, dtype=float))
        return s.rolling(period).mean()

    def _prepare_indicators(self, df):
        df = self._normalize_cols(df)
        if df is None or len(df) == 0 or "close" not in df.columns:
            return df
        
        df = df.copy()
        df["rsi"] = self._calc_rsi(df["close"], self.rsi_period)
        df["sma50"] = self._calc_sma(df["close"], self.sma_period)
        return df

    def _is_confirmation_bar(self, n):
        if self.confirm_interval <= 1:
            return True
        return (n % self.confirm_interval) == 0

    def generate_entry_signal(self, df):
        df = self._prepare_indicators(df)
        if df is None or len(df) == 0:
            return None

        n = len(df)
        last = df.iloc[-1]
        rsi = last.get("rsi", np.nan)
        sma = last.get("sma50", np.nan)
        price = float(last.get("close", np.nan))

        if any(map(lambda x: pd.isna(x), [rsi, sma, price])):
            return None

        # only trade on confirmation bars
        if not self._is_confirmation_bar(n):
            return None

        # long: rsi < 40 and price above sma
        if rsi < self.rsi_long_entry and price > sma:
            return "BUY"

        # short: rsi > 60 and price below sma
        if rsi > self.rsi_short_entry and price < sma:
            return "SELL"

        return None

    def generate_exit_signal(self, df):
        df = self._prepare_indicators(df)
        if df is None or len(df) == 0:
            return None

        last = df.iloc[-1]
        rsi = last.get("rsi", np.nan)
        sma = last.get("sma50", np.nan)
        price = float(last.get("close", np.nan))

        if any(map(lambda x: pd.isna(x), [rsi, sma, price])):
            return None

        # exit long if rsi too high or price drops below sma
        if rsi > self.rsi_long_exit or price < (sma * (1 - self.sma_break_pct)):
            return "CLOSE_LONG"

        # exit short if rsi too low or price breaks above sma
        if rsi < self.rsi_short_exit or price > (sma * (1 + self.sma_break_pct)):
            return "CLOSE_SHORT"

        return None