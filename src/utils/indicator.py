from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator

def add_rsi(df, period=14):
    df["rsi"] = RSIIndicator(df["close"], period).rsi()
    return df

def add_sma(df, period=50):
    df["ma50"] = SMAIndicator(df["close"], period).sma_indicator()
    return df
