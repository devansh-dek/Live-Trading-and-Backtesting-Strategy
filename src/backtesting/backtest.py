from backtesting import Backtest
from src.strategy.multi_tf import MultiTFStrategy

def run_backtest(data):
    bt = Backtest(data, MultiTFStrategy, cash=10000)
    return bt.run()
