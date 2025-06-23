# src/error_handler.py
import logging

logger = logging.getLogger(__name__)


class ErrorHandler:
    def __init__(self):
        logger.info("ErrorHandler initialized.")

    def handle_exception(self, exception: Exception, context: str = "general operation"):
        """
        Logs and processes exceptions for better monitoring.
        """
        error_message = f"An error occurred during {context}: {exception}"
        logger.error(error_message, exc_info=True)
        return error_message

    def log_warning(self, message: str, context: str = "general operation"):
        """Logs a warning message."""
        logger.warning(f"Warning during {context}: {message}")

    def log_info(self, message: str, context: str = "general operation"):
        """Logs an informational message."""
        logger.info(f"Info during {context}: {message}")
    
