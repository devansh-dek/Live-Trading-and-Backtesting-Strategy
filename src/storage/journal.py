"""SQLite trade and signal journal for audit and reconciliation."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Optional

from config.config import DB_PATH


class TradeJournal:
  def __init__(self, db_path: str = DB_PATH):
    self.db_path = db_path
    self._init_schema()

  @contextmanager
  def _conn(self):
    conn = sqlite3.connect(self.db_path)
    conn.row_factory = sqlite3.Row
    try:
      yield conn
      conn.commit()
    finally:
      conn.close()

  def _init_schema(self) -> None:
    with self._conn() as conn:
      conn.executescript("""
        CREATE TABLE IF NOT EXISTS signals (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          ts TEXT NOT NULL,
          symbol TEXT NOT NULL,
          signal TEXT NOT NULL,
          price REAL,
          rsi REAL,
          reason TEXT,
          position TEXT
        );
        CREATE TABLE IF NOT EXISTS trades (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          ts TEXT NOT NULL,
          symbol TEXT NOT NULL,
          side TEXT NOT NULL,
          quantity REAL,
          price REAL,
          order_id TEXT,
          pnl REAL
        );
      """)

  def log_signal(
    self,
    symbol: str,
    signal: str,
    price: float,
    rsi: Optional[float] = None,
    reason: str = "",
    position: str = "FLAT",
  ) -> None:
    with self._conn() as conn:
      conn.execute(
        "INSERT INTO signals (ts, symbol, signal, price, rsi, reason, position) VALUES (?,?,?,?,?,?,?)",
        (datetime.utcnow().isoformat(), symbol, signal, price, rsi, reason, position),
      )

  def log_trade(
    self,
    symbol: str,
    side: str,
    quantity: float,
    price: float,
    order_id: Any = None,
    pnl: Optional[float] = None,
  ) -> None:
    with self._conn() as conn:
      conn.execute(
        "INSERT INTO trades (ts, symbol, side, quantity, price, order_id, pnl) VALUES (?,?,?,?,?,?,?)",
        (datetime.utcnow().isoformat(), symbol, side, quantity, price, str(order_id), pnl),
      )

  def recent_signals(self, limit: int = 50) -> list[dict]:
    with self._conn() as conn:
      rows = conn.execute(
        "SELECT * FROM signals ORDER BY id DESC LIMIT ?", (limit,)
      ).fetchall()
    return [dict(r) for r in rows]

  def recent_trades(self, limit: int = 50) -> list[dict]:
    with self._conn() as conn:
      rows = conn.execute(
        "SELECT * FROM trades ORDER BY id DESC LIMIT ?", (limit,)
      ).fetchall()
    return [dict(r) for r in rows]

  def session_summary(self) -> dict:
    with self._conn() as conn:
      trades = conn.execute("SELECT pnl FROM trades WHERE pnl IS NOT NULL").fetchall()
    pnls = [r[0] for r in trades]
    if not pnls:
      return {"trades": 0, "total_pnl": 0.0, "win_rate": 0.0}
    wins = sum(1 for p in pnls if p > 0)
    return {
      "trades": len(pnls),
      "total_pnl": sum(pnls),
      "win_rate": wins / len(pnls) * 100,
    }
