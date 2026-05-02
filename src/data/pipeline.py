"""Data fetching, validation, and multi-timeframe preparation."""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Optional

import pandas as pd
import requests

from config.config import DATA_DIR, SYMBOL

BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"
INTERVAL_MS = {
  "1m": 60_000,
  "5m": 300_000,
  "15m": 900_000,
  "1h": 3_600_000,
  "4h": 14_400_000,
  "1d": 86_400_000,
}


def normalize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
  rename = {}
  for col in df.columns:
    cl = col.lower().strip()
    if cl in ("open", "high", "low", "close", "volume", "timestamp", "date", "datetime"):
      rename[col] = "timestamp" if cl in ("date", "datetime") else cl
  out = df.rename(columns=rename)
  out.columns = [c.lower() for c in out.columns]

  if "timestamp" in out.columns and not isinstance(out.index, pd.DatetimeIndex):
    out["timestamp"] = pd.to_datetime(out["timestamp"])
    out = out.set_index("timestamp")

  required = ["open", "high", "low", "close"]
  for col in required:
    if col not in out.columns:
      raise ValueError(f"Missing column: {col}")

  if "volume" not in out.columns:
    out["volume"] = 0.0

  out = out.sort_index()
  out = out[~out.index.duplicated(keep="last")]
  return out[["open", "high", "low", "close", "volume"]].astype(float)


def fetch_binance_klines(
  symbol: str = SYMBOL,
  interval: str = "15m",
  start: Optional[datetime] = None,
  end: Optional[datetime] = None,
  limit: int = 1000,
) -> pd.DataFrame:
  """Paginated download from Binance public REST API (no API key required)."""
  if interval not in INTERVAL_MS:
    raise ValueError(f"Unsupported interval: {interval}")

  start_ms = int(start.replace(tzinfo=timezone.utc).timestamp() * 1000) if start else None
  end_ms = int(end.replace(tzinfo=timezone.utc).timestamp() * 1000) if end else None

  all_rows: list[list] = []
  current_start = start_ms

  while True:
    params: dict = {"symbol": symbol, "interval": interval, "limit": limit}
    if current_start is not None:
      params["startTime"] = current_start
    if end_ms is not None:
      params["endTime"] = end_ms

    resp = requests.get(BINANCE_KLINES_URL, params=params, timeout=30)
    resp.raise_for_status()
    batch = resp.json()
    if not batch:
      break

    all_rows.extend(batch)
    last_open = batch[-1][0]
    next_start = last_open + INTERVAL_MS[interval]

    if end_ms is not None and next_start >= end_ms:
      break
    if len(batch) < limit:
      break

    current_start = next_start
    time.sleep(0.2)

  if not all_rows:
    return pd.DataFrame()

  df = pd.DataFrame(
    all_rows,
    columns=[
      "timestamp", "open", "high", "low", "close", "volume",
      "close_time", "quote_volume", "trades", "taker_buy_base",
      "taker_buy_quote", "ignore",
    ],
  )
  df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True).dt.tz_convert(None)
  return normalize_ohlcv(df.set_index("timestamp").reset_index())


def load_or_fetch(
  path: str,
  *,
  symbol: str = SYMBOL,
  interval: str = "15m",
  months: int = 18,
  force: bool = False,
) -> pd.DataFrame:
  os.makedirs(os.path.dirname(path) or DATA_DIR, exist_ok=True)

  if os.path.isfile(path) and not force:
    df = normalize_ohlcv(pd.read_csv(path, parse_dates=["timestamp"]))
    if len(df) >= 500:
      return df

  end = datetime.now(timezone.utc).replace(tzinfo=None)
  start = end - pd.DateOffset(months=months)
  df = fetch_binance_klines(symbol=symbol, interval=interval, start=start, end=end)
  if df.empty:
    raise RuntimeError(f"No data fetched for {symbol} {interval}")

  df.reset_index().to_csv(path, index=False)
  return df


def resample_ohlcv(df: pd.DataFrame, rule: str) -> pd.DataFrame:
  df = normalize_ohlcv(df)
  return df.resample(rule).agg(
    {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
  ).dropna()
