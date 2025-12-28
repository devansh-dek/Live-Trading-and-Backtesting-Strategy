from src.trading.exchange import BinanceExchange
from src.trading.executor import TradeExecutor

if __name__ == "__main__":
    exchange = BinanceExchange()
    executor = TradeExecutor(exchange)

    signal = "BUY"  # test signal
    executor.execute(signal)
