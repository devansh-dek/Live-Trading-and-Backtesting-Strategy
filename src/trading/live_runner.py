"""Live trading loop using the shared signal engine."""

from __future__ import annotations

import logging
import time
from datetime import datetime

from config.config import ENTRY_TIMEFRAME, STRATEGY, SYMBOL
from src.quant.risk import RiskManager
from src.quant.signals import MultiTimeframeSignalEngine, Signal
from src.storage.journal import TradeJournal
from src.trading.executor import TradeExecutor
from src.trading.exchange import BinanceExchange
from src.utils.data import to_dataframe

logger = logging.getLogger(__name__)


class LiveRunner:
  def __init__(
    self,
    exchange: BinanceExchange | None = None,
    executor: TradeExecutor | None = None,
    engine: MultiTimeframeSignalEngine | None = None,
    journal: TradeJournal | None = None,
    risk: RiskManager | None = None,
  ):
    self.exchange = exchange or BinanceExchange()
    self.engine = engine or MultiTimeframeSignalEngine(STRATEGY)
    self.executor = executor or TradeExecutor(self.exchange, logger=logger)
    self.journal = journal or TradeJournal()
    self.risk = risk or RiskManager(STRATEGY)

  def run(
    self,
    symbol: str = SYMBOL,
    timeframe: str = ENTRY_TIMEFRAME,
    fetch_limit: int = 120,
    loop_delay: int = 60,
    max_iterations: int | None = None,
  ) -> None:
    price = self.exchange.get_current_price()
    if price is None or not self.exchange.is_authenticated():
      raise RuntimeError("Exchange unavailable or API keys invalid")

    balance = self.exchange.get_account_balance("USDT")
    logger.info("=" * 70)
    logger.info(
      "Live trading | %s %s | Price: $%s | USDT: $%s",
      symbol, timeframe, f"{price:,.2f}", f"{balance:,.2f}",
    )
    logger.info("=" * 70)

    position = None
    entry_price = entry_quantity = None
    iteration = 0

    try:
      while True:
        iteration += 1
        if max_iterations and iteration > max_iterations:
          logger.info("Completed %d iteration(s)", max_iterations)
          break

        klines = self.exchange.client.get_klines(
          symbol=symbol, interval=timeframe, limit=fetch_limit,
        )
        df = to_dataframe(
          klines,
          ["timestamp", "open", "high", "low", "close", "volume",
           "close_time", "quote_volume", "trades", "taker_buy_base",
           "taker_buy_quote", "ignore"],
        )
        df = df.set_index("timestamp")[["open", "high", "low", "close", "volume"]]

        current_price = self.exchange.get_current_price()
        if current_price is None or len(df) < STRATEGY.sma_slow:
          time.sleep(loop_delay)
          continue

        today = datetime.now().date()
        if self.risk.is_daily_loss_breached(balance, today):
          logger.warning("Daily loss limit reached — skipping new entries")
          time.sleep(loop_delay)
          continue

        if position:
          signal, ctx = self.engine.exit_signal(df, position)
          exit_label = signal.value if signal else "HOLD"
          self.journal.log_signal(
            symbol=symbol, signal=exit_label, price=current_price,
            rsi=ctx.rsi if ctx else None, reason=ctx.reason if ctx else "",
            position=position,
          )
          if signal in (Signal.CLOSE_LONG, Signal.CLOSE_SHORT):
            side = "SELL" if position == "LONG" else "BUY"
            order = self.executor.execute(side, entry_quantity)
            if order:
              pnl = (
                (current_price - entry_price) * entry_quantity
                if position == "LONG"
                else (entry_price - current_price) * entry_quantity
              )
              self.risk.record_pnl(today, pnl)
              self.journal.log_trade(
                symbol, side, entry_quantity, current_price, order.get("orderId"), pnl,
              )
              position = entry_price = entry_quantity = None
            time.sleep(loop_delay)
            continue

        if not position:
          signal, ctx = self.engine.entry_signal(df)
          entry_label = signal.value if signal else "HOLD"
          self.journal.log_signal(
            symbol=symbol, signal=entry_label, price=current_price,
            rsi=ctx.rsi if ctx else None, reason=ctx.reason if ctx else "",
            position="FLAT",
          )
          if signal in (Signal.BUY, Signal.SELL):
            side = signal.value
            order = self.executor.execute(side)
            if order and ctx:
              position = "LONG" if signal == Signal.BUY else "SHORT"
              entry_price = current_price
              entry_quantity = float(order.get("executedQty", 0))
              sl = self.engine.stop_loss(entry_price, ctx.atr, side)
              tp = self.engine.take_profit(entry_price, ctx.atr, side)
              logger.info("Entered %s | qty=%s | SL=%.2f | TP=%.2f", position, entry_quantity, sl, tp)

        logger.info(
          "Iteration %d | Price: $%s | Position: %s",
          iteration, f"{current_price:,.2f}", position or "FLAT",
        )
        time.sleep(loop_delay)

    except KeyboardInterrupt:
      logger.info("Shutdown requested")
      if position and entry_quantity:
        side = "SELL" if position == "LONG" else "BUY"
        self.executor.execute(side, entry_quantity)
