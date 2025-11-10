"""
Simple logging utilities for the reporting pipeline.
"""

from __future__ import annotations
import logging

_LOGGER_NAME = "report_auto"


def get_logger() -> logging.Logger:
    logger = logging.getLogger(_LOGGER_NAME)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("[%(levelname)s] %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


_logger = get_logger()
_seen_once: set[str] = set()


def info(msg: str) -> None:
    _logger.info(msg)


def warn(msg: str) -> None:
    _logger.warning(msg)


def error(msg: str) -> None:
    _logger.error(msg)


def warn_once(msg: str) -> None:
    if msg in _seen_once:
        return
    _seen_once.add(msg)
    _logger.warning(msg)
