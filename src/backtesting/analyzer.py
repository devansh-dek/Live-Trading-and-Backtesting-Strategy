"""Console output for backtest results."""

from src.backtesting.metrics import format_metrics_table


def print_stats(result: dict) -> None:
  metrics = result["metrics"]
  benchmark = result["benchmark"]

  print("=" * 60)
  print("BACKTEST RESULTS")
  print("=" * 60)
  print(format_metrics_table(metrics, "Strategy"))
  print()
  print(format_metrics_table({
    "total_return_pct": benchmark["total_return_pct"],
    "final_equity": benchmark["final_equity"],
    "max_drawdown_pct": "N/A",
    "sharpe_ratio": "N/A",
    "sortino_ratio": "N/A",
    "calmar_ratio": "N/A",
    "num_trades": "N/A",
    "win_rate_pct": "N/A",
    "profit_factor": "N/A",
    "avg_trade_pnl": "N/A",
    "exposure_pct": "N/A",
  }, "Buy & Hold"))
  print("=" * 60)

  if result.get("report_path"):
    print(f"HTML report: {result['report_path']}")

  trades = result.get("trades")
  if trades is not None and len(trades) > 0:
    print(f"Trades saved: data/backtest_trades.csv ({len(trades)} trades)")
