import csv

def log_trade(row, file):
    with open(file, "a") as f:
        writer = csv.writer(f)
        writer.writerow(row)
