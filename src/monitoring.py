import logging
from datetime import datetime


logger = logging.getLogger(__name__)


def log_system_health(message: str, level: str = "info"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    
    if level.lower() == "error":
        logger.error(log_entry)
    elif level.lower() == "warning":
        logger.warning(log_entry)
    elif level.lower() == "debug":
        logger.debug(log_entry)
    else:
        logger.info(log_entry)
