import logging

LOG_DEFAULT_FORMAT = (
    "[%(asctime)s.%(msecs)03d] %(module)10s:%(lineno)-3d %(levelname)-7s - %(message)s"
)


def configure_logger(
    filename: str,
    level: int = logging.INFO,
    format: str = LOG_DEFAULT_FORMAT,
):
    return logging.basicConfig(
        level=level,
        format=format,
        filename=filename,
    )
