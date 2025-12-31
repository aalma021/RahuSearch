import logging
from logging.handlers import RotatingFileHandler
import os

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

LOG_PATH = os.path.join(LOG_DIR, "app.log")

formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    "%Y-%m-%d %H:%M:%S"
)

handler = RotatingFileHandler(LOG_PATH, maxBytes=5_000_000, backupCount=3)
handler.setFormatter(formatter)

console = logging.StreamHandler()
console.setFormatter(formatter)

logger = logging.getLogger("app")
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)
logger.addHandler(console)
