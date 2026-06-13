"""统一日志系统 — 替代散落各处的 print()"""
import logging
import sys

from core.settings import settings


def setup_logger(name: str = "platform") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    level = logging.DEBUG if settings.debug else logging.INFO
    logger.setLevel(level)

    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-7s | %(name)-20s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(fmt)
    logger.addHandler(handler)

    return logger


log = setup_logger()
