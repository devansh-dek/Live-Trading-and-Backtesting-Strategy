"""
Comprehensive logging configuration for the trading system.
Sets up logging for strategy, execution, data, and debugging throughout the system.
"""

import logging
import os
from datetime import datetime


def setup_logging(name=__name__, level=logging.INFO):
    """
    Setup comprehensive logging with both console and file output.

    Args:
        name: Logger name (usually __name__)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Format: [TIMESTAMP] [LEVEL] [MODULE] - MESSAGE
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler (INFO and above)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (DEBUG and above)
    timestamp = datetime.now().strftime('%Y%m%d')
    log_file = f'logs/trading_{timestamp}.log'
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def get_logger(name):
    """
    Get a logger instance with the given name.

    Args:
        name: Logger name (use __name__ in modules)

    Returns:
        logger: Logger instance
    """
    return logging.getLogger(name)


# Module-specific loggers
strategy_logger = setup_logging('strategy', logging.DEBUG)
executor_logger = setup_logging('executor', logging.DEBUG)
exchange_logger = setup_logging('exchange', logging.DEBUG)
backtest_logger = setup_logging('backtest', logging.DEBUG)
data_logger = setup_logging('data', logging.DEBUG)
