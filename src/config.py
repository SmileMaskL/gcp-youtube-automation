# src/config.py

import os
from google.cloud import secretmanager
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO) # Cloud Function은 INFO 레벨 로그도 기본적으로 Cloud Logging에 수집합니다.

class Config:
    def __init__(self):
        logger.info("Config 초기화 시작...")
        
        # 환경 변수 로드
        self.gcp_project_id = os.getenv("GCP_PROJECT_ID")
        self.gcp_bucket_name = os.getenv("GCP_BUCKET_NAME")
        self.elevenlabs_voice_id = os.getenv("ELEVENLABS_VOICE_ID")

        if not self.gcp_project_id:
            logger.critical("환경 변수 GCP_PROJECT_ID가 설정되지 않았습니다.")
            raise ValueError("GCP_PROJECT_ID 환경 변수가 필요합니다.")
        if not self.gcp_bucket_name:
            logger.critical("환경 변수 GCP_BUCKET_NAME이 설정되지 않았습니다.")
            raise ValueError("GCP_BUCKET_NAME 환경 변수가 필요합니다.")
        if not self.elevenlabs_voice_id:
            logger.critical("환경 변수 ELEVENLABS_VOICE_ID가 설정되지 않았습니다.")
            raise ValueError("ELEVENLABS_VOICE_ID 환경 변수가 필요합니다.")

        logger.info(f"GCP_PROJECT_ID: {self.gcp_project_id}")
        logger.info(f"GCP_BUCKET_NAME: {self.gcp_bucket_name}")
        logger.info(f"ELEVENLABS_VOICE_ID: {self.elevenlabs_voice_id}")


        # Secret Manager 클라이언트 초기화 및 시크릿 값 가져오기
        try:
            logger.info("Secret Manager 클라이언트 초기화 시도...")
            self.secret_manager_client = secretmanager.SecretManagerServiceClient()
            logger.info("Secret Manager 클라이언트 초기화 성공.")

            # 시크릿 이름 정의
            self.youtube_client_id_secret_name = self.secret_manager_client.secret_path(self.gcp_project_id, "YOUTUBE_CLIENT_ID")
            self.youtube_client_secret_secret_name = self.secret_manager_client.secret_path(self.gcp_project_id, "YOUTUBE_CLIENT_SECRET")
            self.youtube_refresh_token_secret_name = self.secret_manager_client.secret_path(self.gcp_project_id, "YOUTUBE_REFRESH_TOKEN")
            self.elevenlabs_api_key_secret_name = self.secret_manager_client.secret_path(self.gcp_project_id, "ELEVENLABS_API_KEY")

            # 시크릿 값 로드 (게터 메서드로 변경하여 필요할 때만 호출)
            # 여기서는 초기화 시점에 바로 로드하지 않고, 게터 함수에서 로드하도록 유지합니다.
            # 하지만 디버깅을 위해 이 시점에 한 번씩 시도해 볼 수도 있습니다.

        except Exception as e:
            logger.error(f"Config 초기화 중 Secret Manager 관련 오류 발생: {e}", exc_info=True)
            raise RuntimeError(f"Secret Manager 초기화 실패: {e}") # 여기서 발생한 예외를 명확히 알 수 있도록 합니다.

        logger.info("Config 초기화 완료.")

    # ... 기존 게터 메서드들은 그대로 유지
    def get_youtube_client_id(self):
        try:
            response = self.secret_manager_client.access_secret_version(request={"name": f"{self.youtube_client_id_secret_name}/versions/latest"})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logger.error(f"YOUTUBE_CLIENT_ID 시크릿을 가져오는 데 실패했습니다: {e}", exc_info=True)
            raise

    def get_youtube_client_secret(self):
        try:
            response = self.secret_manager_client.access_secret_version(request={"name": f"{self.youtube_client_secret_secret_name}/versions/latest"})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logger.error(f"YOUTUBE_CLIENT_SECRET 시크릿을 가져오는 데 실패했습니다: {e}", exc_info=True)
            raise

    def get_youtube_refresh_token(self):
        try:
            response = self.secret_manager_client.access_secret_version(request={"name": f"{self.youtube_refresh_token_secret_name}/versions/latest"})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logger.error(f"YOUTUBE_REFRESH_TOKEN 시크릿을 가져오는 데 실패했습니다: {e}", exc_info=True)
            raise

    def get_elevenlabs_api_key(self):
        try:
            response = self.secret_manager_client.access_secret_version(request={"name": f"{self.elevenlabs_api_key_secret_name}/versions/latest"})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logger.error(f"ELEVENLABS_API_KEY 시크릿을 가져오는 데 실패했습니다: {e}", exc_info=True)
            raise
