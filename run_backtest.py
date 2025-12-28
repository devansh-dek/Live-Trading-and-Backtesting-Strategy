import pandas as pd
from src.backtesting.backtest import run_backtest
from src.backtesting.analyzer import print_stats

if __name__ == "__main__":
    data = pd.read_csv("data/historical_data.csv")
    results = run_backtest(data)
    print_stats(results)
