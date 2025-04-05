import logging
import os
import sys


def setup_logger(
    name: str,
    log_file: str = None,
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Настройка логгера с базовой конфигурацией.

    :param name: Имя логгера
    :param log_file: Путь к файлу для записи логов (если None, логи выводятся только в консоль)
    :param level: Уровень логирования (по умолчанию INFO)
    :return: Настроенный логгер
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Проверяем, чтобы не добавлять хендлеры повторно
    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Консольный обработчик
        console_handler = logging.StreamHandler(stream=sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Файловый обработчик, если указан путь
        if log_file:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        logger.propagate = False

    return logger
