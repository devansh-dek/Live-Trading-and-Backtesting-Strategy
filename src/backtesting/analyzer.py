def print_stats(results):
    

    total_trades = results["# Trades"]
    win_rate = results["Win Rate [%]"]
    equity = results["Equity Final [$]"]
    ret = results["Return [%]"]

    print("\n Summary")
    print(f"Total Trades : {total_trades}")
    print(f"Win Rate     : {win_rate}")
    print(f"Final Equity : ${equity:.2f}")
    print(f"Return       : {ret:.2f}%")


    print("=" * 60)
