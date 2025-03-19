import sys
from loguru import logger


LOGGER_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<yellow>{process}</yellow> | "
    "<level>{level: ^7}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)


def init_logger(log_level: str, log_path: str | None) -> None:
    logger.remove()

    logger.add(
        sys.stderr, colorize=True, format=LOGGER_FORMAT, level=log_level
    )
    if log_path:
        logger.add(
            log_path,
            level=log_level,
            format=LOGGER_FORMAT,
            rotation="1 week",
            retention=4,
            compression="zip",
        )
