import logging
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_logger():
    logger = logging.getLogger()

    # Avoid duplicate handlers if called multiple times
    if logger.hasHandlers():
        logger.handlers.clear()

    # Get log level from .env (default INFO if not set)
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    logger.setLevel(log_level)

    # Console handler only
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        "%(asctime)s | [%(levelname)s] | %(filename)s:%(lineno)d | %(name)s: %(message)s",
        "%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)

    logger.addHandler(console_handler)

    return logger
