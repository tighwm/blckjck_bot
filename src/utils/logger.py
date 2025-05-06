import logging
import os
import sys
from typing import Optional


def setup_logger(
        name: str = "app_logger",
        log_file: Optional[str] = None,
        level: str = "info",
        detailed: bool = False,
        log_to_console: bool = True
) -> logging.Logger:
    levels = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL
    }

    if level.lower() not in levels:
        raise ValueError(f"Уровень логирования должен быть одним из: {', '.join(levels.keys())}")

    logger = logging.getLogger(name)
    logger.setLevel(levels[level.lower()])

    logger.handlers = []

    if detailed:
        log_format = "%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    else:
        log_format = "%(asctime)s - %(levelname)s - %(message)s"

    formatter = logging.Formatter(log_format)

    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    if log_to_console or not log_file:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger

