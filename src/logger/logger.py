from loguru import logger


def setup_logger():
    logger.add(
        "logs/debug.log",
        enqueue=True,
        rotation="5 MB",
        colorize=True,
        format="{time:DD-MM-YYYY HH:mm:ss.SSS} | {level} | {message}",
    )
    logger.add("logs/error.log", level="ERROR", enqueue=True)
