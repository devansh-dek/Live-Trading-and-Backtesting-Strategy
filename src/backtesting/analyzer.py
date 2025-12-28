def print_stats(results):
    # Gracefully handle different key names across library versions
    get = lambda k: results.get(k) if hasattr(results, "get") else results[k]

    total_trades = (
        get("Total Trades")
        or get("Total Closed Trades")
        or 0
    )
    win_rate = (
        get("Win Rate %")
        or get("Win Rate [%]")
        or None
    )
    profit = get("Equity Final [$]") if get("Equity Final [$]") is not None else None

    print("Total trades:", total_trades)
    print("Win rate:", win_rate)
    print("Profit:", profit)
