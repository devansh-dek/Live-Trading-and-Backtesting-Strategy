from binance.client import Client
from config.config import API_KEY, API_SECRET

class BinanceExchange:
    def __init__(self):
        self.client = Client(API_KEY, API_SECRET, testnet=True)
