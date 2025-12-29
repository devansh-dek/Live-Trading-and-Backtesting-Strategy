import os
from dotenv import load_dotenv

load_dotenv()

SYMBOL = "BTCUSDT"
ENTRY_TIMEFRAME = "15m"
CONFIRM_TIMEFRAME = "1h"
RISK_PER_TRADE = 0.001 # riskting 0.1 percent of capital

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
