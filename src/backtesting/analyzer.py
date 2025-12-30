def print_stats(results):
    total_trades = results["# Trades"]
    win_rate = results["Win Rate [%]"]
    equity = results["Equity Final [$]"]
    ret = results["Return [%]"]

    print("=" * 50)
    print("BACKTEST RESULTS")
    print("=" * 50)

    print(f"Total Trades:      {total_trades}")
    print(f"Win Rate:          {win_rate:.2f}%")
    print(f"Equity Final:      ${equity:,.2f}")
    print(f"Return:            {ret:.2f}%")

    if total_trades > 0:
        max_dd = results.get("Max. Drawdown [%]", "N/A")
        sharpe = results.get("Sharpe Ratio", "N/A")

        if sharpe is None or sharpe != sharpe:  
            sharpe = "N/A"

        print(f"Max Drawdown:      {max_dd:.2f}%" if max_dd != "N/A" else "Max Drawdown:      N/A")
        print(f"Sharpe Ratio:      {sharpe}")
    else:
        print("Max Drawdown:      N/A")
        print("Sharpe Ratio:      N/A")

    print("=" * 50)