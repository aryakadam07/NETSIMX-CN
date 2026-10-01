"""
NetSimX — Structured Logging Subsystem
Provides console and file logging with educational formatting for network events.
"""

import logging
import sys
from pathlib import Path
from config.settings import PATHS


def get_logger(name: str = "NetSimX", level: int = logging.INFO) -> logging.Logger:
    """Creates and returns a configured logger with console and file output."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)
    logger.propagate = False

    # Format: [2026-10-01 11:42:00] [INFO] [SimulationEngine] Message
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 1. Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    logger.addHandler(console_handler)

    # 2. File Handler
    try:
        PATHS.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(PATHS.LOGS_DIR / "netsimx.log", encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)
    except Exception as exc:
        console_handler.handle(
            logger.makeRecord(
                name, logging.WARNING, __file__, 0,
                f"Could not create file log handler: {exc}", (), None
            )
        )

    return logger
