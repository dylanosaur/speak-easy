import logging
from datetime import datetime
from util import build_hash

def create_custom_logger(name):
    # Create a logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Create a file handler
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    file_handler = logging.FileHandler(f"logs/{name}.log")
    file_handler.setLevel(logging.DEBUG)

    # Create a formatter and add it to the handler
    formatter = logging.Formatter(log_format, datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)

    # Add the file handler to the logger
    logger.addHandler(file_handler)

    return logger

app_logger = create_custom_logger(f'app-{build_hash}')
headers_logger = create_custom_logger(f'headers')