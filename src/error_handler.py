# src/error_handler.py
import logging
import os

logger = logging.getLogger(__name__)

def log_error_and_notify(message: str, level: str = "ERROR", exc_info: bool = False):
    """
    오류를 로깅하고, 필요에 따라 알림을 보냅니다 (예: Slack, Email).
    현재는 로깅만 구현되어 있습니다.

    Args:
        message (str): 오류 메시지.
        level (str): 로깅 레벨 (INFO, WARNING, ERROR, CRITICAL).
        exc_info (bool): 예외 정보(traceback)를 로깅에 포함할지 여부.
    """
    if level.upper() == "INFO":
        logger.info(message)
    elif level.upper() == "WARNING":
        logger.warning(message)
    elif level.upper() == "ERROR":
        logger.error(message, exc_info=exc_info)
    elif level.upper() == "CRITICAL":
        logger.critical(message, exc_info=exc_info)
    else:
        logger.debug(message, exc_info=exc_info) # 기본값

    # TODO: Slack, Email, Discord 등으로 알림을 보내는 로직 추가
    # 예를 들어, 특정 임계값 이상의 오류 발생 시 알림을 보내도록 구현할 수 있습니다.
    # if level.upper() in ["ERROR", "CRITICAL"]:
    #     send_notification_to_slack(message)
    #     send_notification_to_email(message)
    
    logger.info(f"Error/Notification logged: {message}")

# 추가: 알림 함수 (예시)
# def send_notification_to_slack(message: str):
#     # Slack Webhook URL은 GitHub Secret 또는 GCP Secret Manager에 저장
#     slack_webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
#     if slack_webhook_url:
#         try:
#             import requests
#             payload = {"text": f"🚨 YouTube Automation Alert: {message}"}
#             response = requests.post(slack_webhook_url, json=payload)
#             response.raise_for_status()
#             logger.info("Slack notification sent successfully.")
#         except Exception as e:
#             logger.error(f"Failed to send Slack notification: {e}")
