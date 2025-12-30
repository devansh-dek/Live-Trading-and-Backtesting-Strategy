def print_stats(stats):
    """Display backtest results with detailed summary."""

    print("\n" + "="*70)
    print("BACKTEST RESULTS")
    print("="*70)

    if stats['total_trades'] == 0:
        print("No trades executed during backtest.")
        print(f"Final Balance: ${stats['final_balance']:,.2f}")
        print(f"Return: ${stats['total_return']:,.2f} ({stats['return_pct']:.2f}%)")
        print("="*70)
        return

    # Summary stats
    print(f"Total Trades:          {stats['total_trades']}")
    print(f"Winning Trades:        {stats['winning_trades']}")
    print(f"Losing Trades:         {stats['losing_trades']}")
    print(f"Win Rate:              {stats['win_rate']:.2f}%")
    print()
    print(f"Total PnL:             ${stats['total_pnl']:,.2f}")
    print(f"Average PnL/Trade:     ${stats['avg_pnl']:,.2f}")
    print(f"Max Drawdown:          ${stats['max_drawdown']:,.2f}")
    print()
    print(f"Starting Capital:      ${100000:,.2f}")
    print(f"Final Balance:         ${stats['final_balance']:,.2f}")
    print(f"Total Return:          ${stats['total_return']:,.2f}")
    print(f"Return %:              {stats['return_pct']:.2f}%")

    # Trade details
    print()
    print("="*70)
    print("TRADE DETAILS")
    print("="*70)

    for i, trade in enumerate(stats['trades'], 1):
        print(f"\nTrade #{i} ({trade['position']})")
        print(f"  Entry:  Bar {trade['entry_bar']} @ ${trade['entry_price']:,.2f}")
        print(f"  Exit:   Bar {trade['exit_bar']} @ ${trade['exit_price']:,.2f}")
        print(f"  Qty:    {trade['quantity']:.8f}")
        print(f"  PnL:    ${trade['pnl']:,.2f}")
        print(f"  Duration: {trade['duration_bars']} bars")

    print("\n" + "="*70)
