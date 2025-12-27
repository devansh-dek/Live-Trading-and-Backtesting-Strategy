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
├── config/
│   └── config.py           # Configuration settings and API keys
├── src/
│   ├── strategy/
│   │   ├── base.py        # Base strategy class
│   │   └── multi_tf.py    # Multi-timeframe strategy implementation
│   ├── backtesting/
│   │   ├── backtest.py    # Backtesting engine
│   │   └── analyzer.py    # Backtest results analysis
│   ├── trading/
│   │   ├── exchange.py    # Binance API wrapper
│   │   └── executor.py    # Trade execution logic
│   └── utils/
│       ├── logger.py      # Logging utilities
│       └── data.py        # Data handling utilities
└── data/
    ├── backtest_trades.csv    # Backtest trade logs
    └── live_trades.csv        # Live trading logs

```


## Strategy Details

The strategy combines signals from two timeframes:
- 15-minute timeframe for entry signals
- 1-hour timeframe for trade confirmation

Key components:
- Entry signals generated on 15m timeframe
- Trade confirmation using 1h timeframe indicators
- Risk management rules implemented at both timeframes
- Position sizing based on volatility and account equity

## Trade Logging

Both backtest and live trades are logged with:
- Timestamp
- Trade direction (long/short)
- Entry price
- Exit price
- Position size
- PnL
- Additional metadata

## Development Guidelines

- Document all classes and methods
- Use logging for debugging and monitoring

## Dependencies

Key packages used:
- backtesting.py
- python-binance
- pandas
- numpy
- ta (Technical Analysis library)
- python-dotenv

## Notes

- Always test thoroughly on Binance Testnet before live deployment
- Monitor trade execution latency
- Regularly validate strategy performance
- Keep API keys secure and never commit them to version control


## Author

Siddhant, Numatix

## Acknowledgments

- Binance for providing the Testnet API
- backtesting.py library contributors
- Technical Analysis library contributors 