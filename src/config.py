# src/config.py
import os
import json
import logging
from google.cloud import secretmanager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Config:
    def __init__(self):
        # GCP_PROJECT_ID 환경 변수를 확실히 가져오고, 없으면 오류 발생
        self.project_id = os.getenv("GCP_PROJECT_ID")
        if not self.project_id:
            logger.critical("FATAL: GCP_PROJECT_ID environment variable is not set. Cannot proceed.")
            raise ValueError("GCP_PROJECT_ID environment variable is required.")

        self.bucket_name = os.getenv("GCP_BUCKET_NAME")
        self.region = os.getenv("REGION", "us-central1")

        try:
            self.secret_client = secretmanager.SecretManagerServiceClient()
            logger.info("Secret Manager client initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize Secret Manager client: {e}", exc_info=True)
            raise # 클라이언트 초기화 실패는 치명적이므로 예외 발생

        # secret_prefix를 project_id를 사용하여 정확하게 설정
        self.secret_prefix = f"projects/{self.project_id}/secrets"
        logger.info(f"Secret prefix set to: {self.secret_prefix}")

        # Secret Manager에서 API 키 로드 (이전 답변에서 수정 제안했던 내용 유지)
        self.elevenlabs_api_key = self._get_secret("ELEVENLABS_API_KEY")
        self.elevenlabs_voice_id = self._get_secret("ELEVENLABS_VOICE_ID")
        self.news_api_key = self._get_secret("NEWS_API_KEY")
        self.pexels_api_key = self._get_secret("PEXELS_API_KEY")
        self.youtube_client_id = self._get_secret("YOUTUBE_CLIENT_ID")
        self.youtube_client_secret = self._get_secret("YOUTUBE_CLIENT_SECRET")
        self.youtube_refresh_token = self._get_secret("YOUTUBE_REFRESH_TOKEN")

        self.openai_keys_json = json.loads(self._get_secret("OPENAI_KEYS_JSON", is_json=True))
        self.gemini_api_key = self._get_secret("GEMINI_API_KEY")

        self.daily_video_count = int(os.getenv("DAILY_VIDEO_COUNT", 5))
        self.target_video_duration_seconds = int(os.getenv("TARGET_VIDEO_DURATION_SECONDS", 50))

    def _get_secret(self, secret_name: str, is_json: bool = False):
        name = f"{self.secret_prefix}/{secret_name}/versions/latest"
        logger.debug(f"Attempting to access secret: {name}") # 디버그 로그 추가
        try:
            response = self.secret_client.access_secret_version(request={"name": name})
            secret_value = response.payload.data.decode("UTF-8")
            logger.info(f"Secret '{secret_name}' successfully loaded.")
            if is_json:
                return json.loads(secret_value)
            return secret_value
        except Exception as e:
            logger.error(f"Failed to fetch secret '{secret_name}' from '{name}': {e}", exc_info=True) # 경로 포함
            raise ValueError(f"Secret '{secret_name}' could not be loaded. Please check Secret Manager and IAM permissions.")

config = Config()
