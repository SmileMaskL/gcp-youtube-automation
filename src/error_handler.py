import logging
import requests

logger = logging.getLogger(__name__)

def handle_error(message: str, level: str = "ERROR"):
    """오류 처리 및 알림"""
    if level == "ERROR":
        logger.error(message)
    elif level == "WARNING":
        logger.warning(message)
    
    # Slack 알림 (웹훅 URL 필요)
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if webhook_url:
        try:
            payload = {"text": f"🚨 오류 발생: {message}"}
            requests.post(webhook_url, json=payload)
        except Exception as e:
            logger.error(f"Slack 알림 실패: {e}")
