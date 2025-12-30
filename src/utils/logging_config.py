import logging
import os
from datetime import datetime


def setup_logging(name=__name__, level=logging.INFO):
    """Setup logging with console and file output"""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # avoid duplicate handlers
    if logger.handlers:
        return logger

    if not os.path.exists('logs'):
        os.makedirs('logs')

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # console output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # file output
    timestamp = datetime.now().strftime('%Y%m%d')
    log_file = f'logs/trading_{timestamp}.log'
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def get_logger(name):
    """Get logger by name"""
    return logging.getLogger(name)


# module loggers
strategy_logger = setup_logging('strategy', logging.DEBUG)
executor_logger = setup_logging('executor', logging.DEBUG)
exchange_logger = setup_logging('exchange', logging.DEBUG)
backtest_logger = setup_logging('backtest', logging.DEBUG)
data_logger = setup_logging('data', logging.DEBUG)