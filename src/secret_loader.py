# src/secret_loader.py
from google.cloud import secretmanager
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class SecretManager:
    def __init__(self, project_id: Optional[str] = None):
        """
        SecretManager 클라이언트를 초기화합니다.
        프로젝트 ID가 명시적으로 제공되지 않으면 'youtube-fully-automated'를 기본값으로 사용합니다.
        """
        self.client = secretmanager.SecretManagerServiceClient()
        # 프로젝트 ID를 'youtube-fully-automated'로 직접 설정하거나,
        # 초기화 시 project_id 인자가 제공되면 그 값을 사용합니다.
        self.project_id = project_id or "youtube-fully-automated"
        
        if not self.project_id:
            # 이 코드는 project_id가 "youtube-fully-automated"로 설정되었으므로
            # 사실상 도달할 수 없지만, 안전을 위해 유지합니다.
            raise ValueError("GCP 프로젝트 ID가 설정되지 않았습니다")

    def get_secret(self, secret_id: str, version: str = "latest") -> str:
        """
        Google Secret Manager에서 지정된 시크릿을 가져옵니다.

        Args:
            secret_id (str): 가져올 시크릿의 ID입니다.
            version (str): 가져올 시크릿 버전입니다 (예: "latest", "1", "2"). 기본값은 "latest"입니다.

        Returns:
            str: 시크릿의 페이로드 데이터 (UTF-8 디코딩).

        Raises:
            RuntimeError: 시크릿 접근 중 오류가 발생한 경우.
        """
        try:
            name = f"projects/{self.project_id}/secrets/{secret_id}/versions/{version}"
            response = self.client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logger.error(f"🔑 시크릿 로드 실패: {secret_id} | {str(e)}")
            raise RuntimeError(f"시크릿 접근 오류: {secret_id}")

# 전역 인스턴스 초기화
# 이제 이 인스턴스는 'youtube-fully-automated' 프로젝트 ID를 사용합니다.
secret_manager = SecretManager()
