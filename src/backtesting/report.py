"""HTML backtest report with equity curve and drawdown charts."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

from config.config import REPORTS_DIR
from src.backtesting.metrics import format_metrics_table


def generate_report(
  equity_curve: pd.Series,
  trades: pd.DataFrame,
  metrics: dict[str, Any],
  benchmark_metrics: dict[str, Any],
  *,
  title: str = "Multi-Timeframe Strategy Backtest",
  output_dir: str = REPORTS_DIR,
) -> str:
  os.makedirs(output_dir, exist_ok=True)
  ts = datetime.now().strftime("%Y%m%d_%H%M%S")
  chart_path = os.path.join(output_dir, f"equity_{ts}.png")
  html_path = os.path.join(output_dir, f"backtest_report_{ts}.html")

  _plot_equity_and_drawdown(equity_curve, chart_path, title)

  trades_html = ""
  if trades is not None and len(trades) > 0:
    display = trades.head(50).copy()
    trades_html = display.to_html(classes="trades", index=False, float_format="%.4f")

  html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 2rem; background: #0f1117; color: #e6e6e6; }}
    h1, h2 {{ color: #58a6ff; }}
    pre {{ background: #161b22; padding: 1rem; border-radius: 8px; overflow-x: auto; }}
    img {{ max-width: 100%; border-radius: 8px; margin: 1rem 0; }}
    table.trades {{ border-collapse: collapse; width: 100%; font-size: 0.85rem; }}
    table.trades th, table.trades td {{ border: 1px solid #30363d; padding: 0.4rem 0.6rem; text-align: right; }}
    table.trades th {{ background: #161b22; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }}
    @media (max-width: 900px) {{ .grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>

  <div class="grid">
    <div>
      <h2>Strategy Metrics</h2>
      <pre>{format_metrics_table(metrics, "Strategy")}</pre>
    </div>
    <div>
      <h2>Buy &amp; Hold Benchmark</h2>
      <pre>{format_metrics_table(benchmark_metrics, "Benchmark")}</pre>
    </div>
  </div>

  <h2>Equity Curve &amp; Drawdown</h2>
  <img src="{os.path.basename(chart_path)}" alt="Equity curve">

  <h2>Recent Trades (up to 50)</h2>
  {trades_html or "<p>No trades recorded.</p>"}
</body>
</html>"""

  with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)

  return html_path


def _plot_equity_and_drawdown(equity: pd.Series, path: str, title: str) -> None:
  fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), sharex=True, gridspec_kw={"height_ratios": [3, 1]})

  idx = equity.index
  ax1.plot(idx, equity.values, color="#58a6ff", linewidth=1.2, label="Equity")
  ax1.set_ylabel("Equity ($)")
  ax1.set_title(title)
  ax1.legend(loc="upper left")
  ax1.grid(True, alpha=0.3)
  ax1.set_facecolor("#161b22")
  fig.patch.set_facecolor("#0f1117")
  ax1.tick_params(colors="#e6e6e6")
  ax1.title.set_color("#e6e6e6")
  ax1.yaxis.label.set_color("#e6e6e6")

  peak = equity.cummax()
  dd = (equity - peak) / peak * 100
  ax2.fill_between(idx, dd.values, 0, color="#f85149", alpha=0.6)
  ax2.set_ylabel("DD %")
  ax2.set_xlabel("Date")
  ax2.grid(True, alpha=0.3)
  ax2.set_facecolor("#161b22")
  ax2.tick_params(colors="#e6e6e6")

  if isinstance(idx, pd.DatetimeIndex):
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    fig.autofmt_xdate()

  plt.tight_layout()
  plt.savefig(path, dpi=120, facecolor=fig.get_facecolor())
  plt.close(fig)
