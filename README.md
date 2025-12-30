[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/osVrZZ-X)
# Multi-Timeframe Trading Strategy

A sophisticated trading system that implements a multi-timeframe strategy using Python, with both backtesting and live trading capabilities on Binance Testnet.

## Project Overview

This project implements a trading strategy that combines multiple timeframes (15-minute entries with 1-hour confirmations) to make trading decisions. The system includes both backtesting capabilities using `backtesting.py` and live trading functionality through Binance Testnet API.

### Key Features

- Multi-timeframe strategy implementation (15m entries, 1h confirmations)
- Comprehensive backtesting system with detailed trade logging
- Live trading integration with Binance Testnet
- Trade comparison and analysis tools
- Modular, class-based architecture for maintainability and extensibility

## Project Structure

```
├── README.md
├── requirements.txt
├── .env.example              # Template for API credentials
├── run_backtest.py           # Run backtesting
├── run_live.py               # Run live trading
├── config/
│   └── config.py             # Configuration settings and API keys
├── src/
│   ├── strategy/
│   │   ├── base.py           # Base strategy class
│   │   └── multi_tf.py       # Multi-timeframe strategy implementation
│   ├── backtesting/
│   │   ├── backtest.py       # Backtesting engine
│   │   └── analyzer.py       # Backtest results analysis
│   ├── trading/
│   │   ├── exchange.py       # Binance API wrapper
│   │   └── executor.py       # Trade execution logic
│   └── utils/
│       ├── logger.py         # Logging utilities
│       ├── indicator.py      # Technical indicators
│       └── data.py           # Data handling utilities
└── data/
    ├── historical_data.csv   # Historical price data for backtesting
    ├── backtest_trades.csv   # Backtest trade logs
    └── live_trades.csv       # Live trading logs
```

## Quick Start

### 1. Installation

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Backtest

The backtesting system is ready to use with the included historical data:

```bash
python run_backtest.py
```

Expected output:
```
==================================================
BACKTEST RESULTS
==================================================
Total Trades:      1
Win Rate:          0.00%
Equity Final:      $99,680.59
Return:            -0.32%
Max Drawdown:      -0.32%
Sharpe Ratio:      N/A
==================================================
```

Trades are automatically saved to `data/backtest_trades.csv`.

### 3. Set Up Live Trading (Optional)

**⚠️ WARNING: Live trading executes real orders on Binance Testnet. Never use real API keys!**

#### Step 1: Get Testnet API Keys

1. Visit [Binance Testnet](https://testnet.binance.vision/)
2. Create an account or log in
3. Generate API Key and Secret

#### Step 2: Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your testnet credentials
nano .env  # or use your preferred editor
```

Update `.env` with your credentials:
```
BINANCE_API_KEY=your_testnet_api_key_here
BINANCE_API_SECRET=your_testnet_api_secret_here
```

#### Step 3: Test Connection

```bash
python run_live.py
```

This will verify your API connection and display current balance without executing trades.

## Strategy Details

The strategy combines signals from two timeframes:
- **15-minute timeframe** for entry signals
- **1-hour timeframe** for trade confirmation (simulated by checking every 4th bar)

### Entry Signals

- **Long Entry**: RSI < 40 (oversold) on a confirmation bar (every 4 bars)
- **Short Entry**: RSI > 60 (overbought) on a confirmation bar

### Exit Signals

- **Long Exit**: RSI > 70 (overbought) OR price drops 0.5% below SMA50
- **Short Exit**: RSI < 30 (oversold) OR price rises 0.5% above SMA50

### Risk Management

- Position sizing: 95% of available equity per trade
- Commission: 0.2% per trade (backtesting)
- Live trading: Uses `RISK_PER_TRADE` from config (default 1% of balance)

## Configuration

Edit `config/config.py` to customize:

```python
SYMBOL = "BTCUSDT"           # Trading pair
ENTRY_TIMEFRAME = "15m"      # Entry signal timeframe
CONFIRM_TIMEFRAME = "1h"     # Confirmation timeframe
RISK_PER_TRADE = 0.01        # Risk 1% per trade (live trading)
```

## Trade Logging

### Backtest Trades (`data/backtest_trades.csv`)

Logged automatically during backtesting with columns:
- Size, Entry/Exit Bar, Entry/Exit Price
- PnL, Commission, Return %
- Entry/Exit Time, Duration
- Indicator values at entry and exit

### Live Trades (`data/live_trades.csv`)

Logged when executing live trades with columns:
- Timestamp, Side (BUY/SELL)
- Quantity, Price
- Order ID, Status

## Development Guidelines

### Adding New Indicators

Add indicator functions to `src/utils/indicator.py`:

```python
def add_macd(df, fast=12, slow=26, signal=9):
    """Add MACD indicator to dataframe."""
    # Implementation here
    return df
```

### Customizing the Strategy

Extend or modify `src/strategy/multi_tf.py`:

1. Override `init()` to add custom indicators
2. Modify `next()` to implement your entry/exit logic
3. Adjust parameters like `rsi_period`, `sma_period`, `confirm_interval`

### Testing

Always test thoroughly:

1. **Backtest first**: Validate strategy logic with historical data
2. **Paper trade**: Use Binance Testnet before real trading
3. **Monitor logs**: Check `trading.log` for live trading activity

## Troubleshooting

### Common Issues

**"Broker canceled order due to insufficient margin"**
- Solution: Increase `cash` parameter in `backtest.py` or reduce position size

**"Failed to connect to Binance Testnet"**
- Verify API keys in `.env` file
- Check that keys are from testnet.binance.vision (not regular Binance)
- Ensure internet connection is active

**"No trades executed in backtest"**
- Check if historical data has enough rows (needs 50+ for SMA calculation)
- Adjust RSI thresholds if market conditions don't trigger signals
- Verify `confirm_interval` aligns with data frequency

## Dependencies

Key packages used:
- **backtesting** - Backtesting framework
- **python-binance** - Binance API wrapper
- **pandas** - Data manipulation
- **numpy** - Numerical computations
- **ta** - Technical Analysis library
- **python-dotenv** - Environment variable management

Install all dependencies:
```bash
pip install -r requirements.txt
```

## Performance Metrics

The analyzer displays:
- **Total Trades**: Number of completed trades
- **Win Rate**: Percentage of profitable trades
- **Equity Final**: Final portfolio value
- **Return**: Total return percentage
- **Max Drawdown**: Largest peak-to-trough decline
- **Sharpe Ratio**: Risk-adjusted return metric

## Safety Notes

- ⚠️ **NEVER** commit `.env` file or API keys to version control
- ⚠️ Always test on Testnet before using real funds
- ⚠️ Monitor live trades actively; automated trading carries risk
- ⚠️ Start with small position sizes

## Future Enhancements

- [ ] Real-time data streaming for live trading
- [ ] Multiple symbol support
- [ ] Advanced order types (limit, stop-loss)
- [ ] Telegram/Discord notifications
- [ ] Performance dashboard with charts
- [ ] Parameter optimization using `.optimize()`

## Author

**Siddhant, Numatix**

**Implementation by:** Devansh

## Acknowledgments

- Binance for providing the Testnet API
- backtesting.py library contributors
- Technical Analysis library contributors

## License

This project is for educational purposes. Use at your own risk.