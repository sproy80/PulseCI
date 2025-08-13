# backend/app/utils/logger.py
from loguru import logger
import sys

logger.remove()
logger.add(sys.stdout, colorize=True,
           format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}")


def get_logger():
    return logger
