import sys
import logging

LOG_DEFAULT_FORMAT = (
    "[%(asctime)s.%(msecs)03d] %(module)10s:%(lineno)-3d %(levelname)-7s - %(message)s"
)


def configure_logger(
    filename: str | None = None,
    level: int = logging.INFO,
    format: str = LOG_DEFAULT_FORMAT,
):
    if filename:
        return logging.basicConfig(
            level=level,
            format=format,
            filename=filename,
        )
    return logging.basicConfig(
        level=level,
        format=format,
        stream=sys.stdout,
    )
