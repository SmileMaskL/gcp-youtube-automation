import logging
import sys
from google.cloud import logging as cloud_logging  # 수정된 임포트

class ErrorHandler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # GCP Cloud Logging 설정
        try:
            self.cloud_logger = cloud_logging.Client().logger('youtube_automation')
        except Exception as e:
            self.logger.error(f"Cloud Logging 초기화 실패: {e}")
            self.cloud_logger = None

    def handle(self, error):
        error_msg = f"🚨 심각한 오류 발생: {str(error)}"
        
        # 로컬 로깅
        self.logger.error(error_msg)
        
        # GCP Cloud Logging
        if self.cloud_logger:
            self.cloud_logger.log_text(error_msg, severity='ERROR')
        
        # Slack/이메일 알림 (추가 구현)
        self._send_alert(error_msg)

    def _send_alert(self, message):
        """추가 알림 시스템 (구현 필요)"""
        pass
