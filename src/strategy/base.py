import numpy as np
import pandas as pd


class BaseStrategy:
    """
    Base strategy for live/paper trading signal generation on 15m data
    with 1h confirmation simulated by every 4th bar.

    Methods return simple string signals:
    - generate_entry_signal(df) -> "BUY" | "SELL" | None
    - generate_exit_signal(df)  -> "CLOSE_LONG" | "CLOSE_SHORT" | None

    Expected df columns (case-insensitive): open, high, low, close, volume
    """

    rsi_period = 14
    sma_period = 50
    confirm_interval = 4  # 15m -> 1h confirmation

    rsi_long_entry = 40
    rsi_short_entry = 60
    rsi_long_exit = 70
    rsi_short_exit = 30
    sma_break_pct = 0.005  # 0.5%

    def _normalize_cols(self, df: pd.DataFrame) -> pd.DataFrame:
        if df is None or len(df) == 0:
            return df
        cols = {c: c.lower() for c in df.columns}
        out = df.rename(columns=cols)
        # Ensure canonical names
        rename = {}
        for src, dst in {
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "volume": "volume",
        }.items():
            if src in out.columns:
                rename[src] = dst
        return out.rename(columns=rename)

    def _calc_rsi(self, close: pd.Series, period: int) -> pd.Series:
        s = pd.Series(np.asarray(close, dtype=float))
        delta = s.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
        avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calc_sma(self, close: pd.Series, period: int) -> pd.Series:
        s = pd.Series(np.asarray(close, dtype=float))
        return s.rolling(period).mean()

    def _prepare_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self._normalize_cols(df)
        if df is None or len(df) == 0 or "close" not in df.columns:
            return df
        df = df.copy()
        df["rsi"] = self._calc_rsi(df["close"], self.rsi_period)
        df["sma50"] = self._calc_sma(df["close"], self.sma_period)
        return df

    def _is_confirmation_bar(self, n: int) -> bool:
        if self.confirm_interval <= 1:
            return True
        return (n % self.confirm_interval) == 0

    def generate_entry_signal(self, df: pd.DataFrame):
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

        # Only trade on confirmation bars
        if not self._is_confirmation_bar(n):
            return None

        # Long entry: RSI < 40 and price > SMA
        if rsi < self.rsi_long_entry and price > sma:
            return "BUY"

        # Short entry: RSI > 60 and price < SMA
        if rsi > self.rsi_short_entry and price < sma:
            return "SELL"

        return None

    def generate_exit_signal(self, df: pd.DataFrame):
        df = self._prepare_indicators(df)
        if df is None or len(df) == 0:
            return None

        last = df.iloc[-1]
        rsi = last.get("rsi", np.nan)
        sma = last.get("sma50", np.nan)
        price = float(last.get("close", np.nan))

        if any(map(lambda x: pd.isna(x), [rsi, sma, price])):
            return None

        # Long exit: RSI > 70 OR price < SMA50 - 0.5%
        if rsi > self.rsi_long_exit or price < (sma * (1 - self.sma_break_pct)):
            return "CLOSE_LONG"

        # Short exit: RSI < 30 OR price > SMA50 + 0.5%
        if rsi < self.rsi_short_exit or price > (sma * (1 + self.sma_break_pct)):
            return "CLOSE_SHORT"

        return None
