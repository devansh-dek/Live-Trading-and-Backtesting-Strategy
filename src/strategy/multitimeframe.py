from .base import BaseStrategy
from src.utils.indicator import add_rsi, add_sma

class MultiTFStrategy(BaseStrategy):
    def generate_entry_signal(self, df15, df1h):
        df15 = add_rsi(df15)
        df1h = add_sma(df1h)

        latest15 = df15.iloc[-1]
        latest1h = df1h.iloc[-1]

        if latest15["rsi"] < 30 and latest15["close"] > latest1h["ma50"]:
            return "BUY"
        elif latest15["rsi"] > 70 and latest15["close"] < latest1h["ma50"]:
            return "SELL"
        return "NONE"
