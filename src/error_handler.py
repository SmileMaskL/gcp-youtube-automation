import logging

logger = logging.getLogger(__name__)

def log_error_and_notify(message: str, level: str = "ERROR", exc_info: bool = False):
    if level.upper() == "INFO":
        logger.info(message)
    elif level.upper() == "WARNING":
        logger.warning(message)
    elif level.upper() == "ERROR":
        logger.error(message, exc_info=exc_info)
    elif level.upper() == "CRITICAL":
        logger.critical(message, exc_info=exc_info)
    else:
        logger.debug(message, exc_info=exc_info)
    
    logger.info(f"Error/Notification logged: {message}")

def send_notification_to_slack(message: str):
    slack_webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if slack_webhook_url:
        try:
            import requests
            payload = {"text": f"🚨 YouTube Automation Alert: {message}"}
            response = requests.post(slack_webhook_url, json=payload)
            response.raise_for_status()
            logger.info("Slack notification sent successfully.")
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
