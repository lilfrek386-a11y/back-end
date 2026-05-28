import logging
import sys
from app.core.config import settings


def setup_logging():

    formatter = logging.Formatter(
        fmt="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()

    if not root_logger.handlers:
        root_logger.addHandler(console_handler)

    root_logger.setLevel(settings.log.LEVEL)
