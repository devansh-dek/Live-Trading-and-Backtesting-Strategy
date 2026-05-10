import csv
import os


def log_trade(row, file):
    """Log trade to CSV, creates file if needed"""
    # set headers based on file type
    if "backtest" in file:
        headers = ["EntryTime", "Size", "EntryBar", "EntryPrice", "ExitBar",
                   "ExitPrice", "PnL", "Duration"]
    else:
        headers = ["Timestamp", "Side", "Quantity", "Price", "OrderID", "Status"]

    file_exists = os.path.isfile(file)

    with open(file, "a", newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(headers)
        writer.writerow(row)


def log_trade_detailed(trade_data, file="data/trade_analysis.csv"):
    """Log detailed trade with indicators and reasoning"""
    headers = [
        "Timestamp", "Side", "EntryPrice", "Quantity", "RSI", "SMA",
        "Reason", "RiskPct", "PositionSize"
    ]

    file_exists = os.path.isfile(file)

    with open(file, "a", newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(headers)

        row = [
            trade_data.get('timestamp', ''),
            trade_data.get('side', ''),
            trade_data.get('entry_price', ''),
            trade_data.get('quantity', ''),
            trade_data.get('rsi', ''),
            trade_data.get('sma', ''),
            trade_data.get('reason', ''),
            trade_data.get('risk_pct', ''),
            trade_data.get('position_size', '')
        ]
        writer.writerow(row)


def log_signal(signal_data, file="logs/signals.csv"):
    """Log all strategy signals including skipped ones"""
    headers = [
        "Timestamp", "Bar", "Price", "Signal", "RSI", "SMA",
        "Reason", "PositionStatus"
    ]

    file_exists = os.path.isfile(file)

    with open(file, "a", newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(headers)

        row = [
            signal_data.get('timestamp', ''),
            signal_data.get('bar', ''),
            signal_data.get('price', ''),
            signal_data.get('signal', ''),
            signal_data.get('rsi', ''),
            signal_data.get('sma', ''),
            signal_data.get('reason', ''),
            signal_data.get('position_status', '')
        ]
        writer.writerow(row)


def ensure_data_dir():
    """Make sure data and logs dirs exist"""
    for directory in ['data', 'logs']:
        if not os.path.exists(directory):
            os.makedirs(directory)