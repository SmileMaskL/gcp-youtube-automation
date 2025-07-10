# src/secret_loader.py
from google.cloud import secretmanager
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class SecretManager:
    def __init__(self, project_id: Optional[str] = None):
        self.client = secretmanager.SecretManagerServiceClient()
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        
        if not self.project_id:
            raise ValueError("GCP 프로젝트 ID가 설정되지 않았습니다")

    def get_secret(self, secret_id: str, version: str = "latest") -> str:
        try:
            name = f"projects/{self.project_id}/secrets/{secret_id}/versions/{version}"
            response = self.client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logger.error(f"🔑 시크릿 로드 실패: {secret_id} | {str(e)}")
            raise RuntimeError(f"시크릿 접근 오류: {secret_id}")

# 전역 인스턴스 초기화
secret_manager = SecretManager()
