# src/monitoring.py
import logging
from google.cloud import logging as cloud_logging

logger = logging.getLogger(__name__)


class Monitoring:
    def __init__(self, project_id):
        self.project_id = project_id
        self.client = cloud_logging.Client(project=self.project_id)
        self.logger = self.client.logger('youtube-shorts-automation-log')
        logger.info("Monitoring initialized with Cloud Logging.")

    def log_event(self, severity, message, labels=None):
        """
        Logs an event to Google Cloud Logging.
        """
        if labels is None:
            labels = {}
        self.logger.log_text(message, severity=severity, labels=labels)
        logger.info(f"Cloud Logging: [{severity}] {message}")

    def track_usage(self, api_name, usage_type, value, unit="units"):
        """
        Tracks API usage and logs it.
        """
        message = f"Usage tracking for {api_name}: {usage_type}={value} {unit}"
        labels = {
            "api_name": api_name,
            "usage_type": usage_type,
            "unit": unit
        }
        self.log_event('INFO', message, labels)

    def report_error(self, error_type, error_message, stacktrace=None):
        """
        Reports an error to Google Cloud Logging with ERROR severity.
        """
        message = f"Error: {error_type} - {error_message}"
        labels = {
            "error_type": error_type
        }
        if stacktrace:
            message += f"\nStacktrace:\n{stacktrace}"
        self.log_event('ERROR', message, labels)
    
