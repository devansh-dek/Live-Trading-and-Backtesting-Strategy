# Live Trading System - Usage Guide

## Complete Implementation Summary

Your multi-timeframe trading system is now **fully functional** with the following components:

### ✅ Completed Components

1. **`src/trading/executor.py`** - Trade execution with optional quantity parameter, risk-based sizing, balance validation
2. **`src/strategy/base.py`** - Complete strategy class with RSI + SMA indicators, multi-timeframe confirmation
3. **`src/strategy/multi_tf.py`** - Backtesting-compatible strategy with edge-case handling
4. **`run_live.py`** - Full live trading loop with position tracking and trade summary

---

## How to Use

### Option 1: Run Live Trading Demo (No API Keys Required)

Test the system using historical data to simulate real-time behavior:

```bash
source venv/bin/activate
python demo_live_trading.py
```

This will:
- Simulate bar-by-bar trading
- Track positions (LONG/SHORT)
- Execute entries and exits based on strategy signals
- Display trade summary with PnL

### Option 2: Run Backtesting

Test strategy on historical data:

```bash
source venv/bin/activate
python run_backtest.py
```

### Option 3: Run Live Trading on Binance Testnet

**⚠️ WARNING: Executes real orders on Binance Testnet**

#### Prerequisites:
1. Get API keys from [Binance Testnet](https://testnet.binance.vision/)
2. Create `.env` file:
   ```bash
   cp .env.example .env
   nano .env  # Add your API keys
   ```

#### Run:
```bash
source venv/bin/activate
python run_live.py
```

The script will:
1. Connect to Binance Testnet
2. Display current price and balance
3. Fetch market data every 60 seconds
4. Generate trading signals using the multi-timeframe strategy
5. Execute BUY/SELL orders automatically
6. Track positions and log all trades
7. Display trade summary when stopped (Ctrl+C)

---

## Strategy Details

### Multi-Timeframe Logic
- **Entry Timeframe**: 15 minutes
- **Confirmation**: Every 4 bars (simulates 1-hour confirmation)
- Trades only execute when both timeframes align

### Indicators
- **RSI (14)**: Momentum indicator
- **SMA (50)**: Trend direction

### Entry Rules
- **LONG Entry**: RSI < 40 (oversold) AND price > SMA50 AND confirmation bar
- **SHORT Entry**: RSI > 60 (overbought) AND price < SMA50 AND confirmation bar

### Exit Rules
- **LONG Exit**: RSI > 70 OR price < (SMA50 - 0.5%)
- **SHORT Exit**: RSI < 30 OR price > (SMA50 + 0.5%)

### Risk Management
- Position size: 1% of available balance per trade (configurable in `config/config.py`)
- Commission: 0.2% per trade (backtesting)

---

## Live Trading Flow

```
┌─────────────────────────────────────────┐
│  1. Fetch Market Data (100 bars)       │
│     - 15-minute OHLCV from Binance      │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│  2. Calculate Indicators                │
│     - RSI (14-period)                   │
│     - SMA (50-period)                   │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│  3. Check Position Status               │
└─────────────────┬───────────────────────┘
                  │
         ┌────────┴────────┐
         │                 │
         ▼                 ▼
    IN POSITION       NO POSITION
         │                 │
         ▼                 ▼
  ┌────────────┐    ┌────────────┐
  │ Check Exit │    │Check Entry │
  │  Signal    │    │  Signal    │
  └──────┬─────┘    └──────┬─────┘
         │                 │
         ▼                 ▼
  ┌────────────┐    ┌────────────┐
  │ Execute    │    │ Execute    │
  │ SELL/BUY   │    │ BUY/SELL   │
  └──────┬─────┘    └──────┬─────┘
         │                 │
         └────────┬────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│  4. Log Trade to CSV                    │
│     - data/live_trades.csv              │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│  5. Wait 60 seconds                     │
└─────────────────┬───────────────────────┘
                  │
                  └─────► Repeat
```

---

## Live Trading Session Example

When you run `python run_live.py`, you'll see:

```
==================================================
Starting Live Trading System
==================================================
✓ Connected to Binance Testnet
  Symbol: BTCUSDT
  Current Price: $42,345.67
  USDT Balance: $10,000.00

==================================================
LIVE TRADING SIMULATION
==================================================
Strategy: Multi-Timeframe RSI + SMA
Timeframe: 15m (confirmation every 4 bars)
Symbol: BTCUSDT

Press Ctrl+C to stop trading and view summary
==================================================

--- Iteration 1 ---
Current Price: $42,345.67 | Position: NONE
Waiting 60 seconds before next check...

--- Iteration 2 ---
ENTRY SIGNAL: BUY at $42,320.15
✓ Entered LONG position: 0.002365 @ $42,320.15
Current Price: $42,320.15 | Position: LONG
Waiting 60 seconds before next check...

--- Iteration 3 ---
Current Price: $42,450.20 | Position: LONG
Waiting 60 seconds before next check...

--- Iteration 4 ---
EXIT SIGNAL: CLOSE_LONG at $42,580.30
✓ Exited LONG position: 0.002365 @ $42,580.30 | PnL: $0.62
Current Price: $42,580.30 | Position: NONE
Waiting 60 seconds before next check...
```

When stopped (Ctrl+C):

```
==================================================
LIVE TRADING SESSION SUMMARY
==================================================
Total Trades:          1
Winning Trades:        1
Losing Trades:         0
Win Rate:              100.00%
Total PnL:             $0.62
Average PnL/Trade:     $0.62

Trade Details:
------------------------------------------------------
Trade #1 (LONG)
  Entry:  2025-12-29 14:23:45 @ $42,320.15
  Exit:   2025-12-29 14:28:12 @ $42,580.30
  PnL:    $0.62 | Duration: 4.5 min

==================================================
```

---

## Files Generated

### `data/live_trades.csv`
Contains detailed log of all executed trades:
```csv
Timestamp,Side,Quantity,Price,OrderID,Status
2025-12-29T14:23:45,BUY,0.002365,42320.15,12345678,FILLED
2025-12-29T14:28:12,SELL,0.002365,42580.30,12345679,FILLED
```

### `trading.log`
Detailed system logs with timestamps, errors, and debug info.

---

## Configuration

Edit `config/config.py` to customize:

```python
SYMBOL = "BTCUSDT"           # Trading pair
ENTRY_TIMEFRAME = "15m"      # Data timeframe
CONFIRM_TIMEFRAME = "1h"     # Confirmation timeframe
RISK_PER_TRADE = 0.01        # 1% risk per trade
```

Edit strategy parameters in `src/strategy/base.py`:

```python
rsi_period = 14              # RSI lookback
sma_period = 50              # SMA lookback
confirm_interval = 4         # Bars per confirmation (15m x 4 = 1h)
rsi_long_entry = 40          # Long entry threshold
rsi_short_entry = 60         # Short entry threshold
rsi_long_exit = 70           # Long exit threshold
rsi_short_exit = 30          # Short exit threshold
sma_break_pct = 0.005        # 0.5% SMA break threshold
```

---

## Safety Features

✅ **Position tracking** - Prevents duplicate entries
✅ **Balance validation** - Checks available funds before trading
✅ **Quantity rounding** - Ensures exchange precision requirements
✅ **Error handling** - Graceful failure with logging
✅ **NaN protection** - Skips trading when indicators aren't ready
✅ **Confirmation bars** - Reduces false signals from single timeframe
✅ **Trade logging** - Full audit trail in CSV
✅ **Testnet-only** - Exchange hardcoded to testnet (no real funds risk)

---

## Stopping the System

Press `Ctrl+C` to gracefully stop:
- Closes any open positions
- Displays trade summary
- Logs final state

---

## Next Steps

1. **Paper Trade**: Run on Binance Testnet for a week to validate strategy
2. **Optimize**: Use `backtesting.py`'s `.optimize()` to tune parameters
3. **Monitor**: Add Telegram/Discord notifications for trades
4. **Scale**: Test with multiple symbols in parallel
5. **Risk**: Add stop-loss and take-profit levels
6. **Data**: Integrate WebSocket for true real-time streaming

---

## Troubleshooting

**"No trades executing"**
- Check if indicators are ready (need 50+ bars for SMA)
- Verify confirmation bar logic (trades only every 4th bar)
- Adjust RSI thresholds if market isn't volatile enough

**"Insufficient balance"**
- Reduce `RISK_PER_TRADE` in config.py
- Check Testnet balance (get free funds from faucet)

**"API connection failed"**
- Verify API keys in `.env` file
- Check keys are from testnet.binance.vision
- Ensure IP isn't rate-limited

---

## Summary

Your trading system is **production-ready** for Binance Testnet! All components are:
- ✅ Fully implemented
- ✅ Edge-case protected
- ✅ Tested and working
- ✅ Well-documented

Ready to trade! 🚀
