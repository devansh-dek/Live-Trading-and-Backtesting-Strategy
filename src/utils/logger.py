import csv
import os

def log_trade(row, file):
    """
    Log a trade to CSV file. Creates file with header if it doesn't exist.

    Args:
        row: List of values to log
        file: Path to CSV file
    """
    # Define headers based on file type
    if "backtest" in file:
        headers = ["EntryTime", "Size", "EntryPrice", "ExitPrice", "PnL"]
    else:  # live trades
        headers = ["Timestamp", "Side", "Quantity", "Price", "OrderID", "Status"]

    # Check if file exists to determine if we need to write headers
    file_exists = os.path.isfile(file)

    with open(file, "a", newline='') as f:
        writer = csv.writer(f)

        # Write header if file is new
        if not file_exists:
            writer.writerow(headers)

        writer.writerow(row)




