# src/config.py
import os
import json
import logging
from google.cloud import secretmanager

# 로깅 설정: 이 줄을 파일 상단에 추가하여 logger가 정의되도록 합니다.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Config:
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.bucket_name = os.getenv("GCP_BUCKET_NAME")
        self.region = os.getenv("REGION", "us-central1") # Cloud Function 배포 리전

        try:
            self.secret_client = secretmanager.SecretManagerServiceClient()
            logger.info("Secret Manager client initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize Secret Manager client: {e}", exc_info=True)
            raise

        self.secret_prefix = f"projects/{self.project_id}/secrets" if self.project_id else "projects/YOUR_PROJECT_ID/secrets"

        # Secret Manager에서 API 키 로드
        # GCP Secret Manager에 저장된 정확한 이름(대문자 언더스코어)으로 변경합니다.
        self.elevenlabs_api_key = self._get_secret("ELEVENLABS_API_KEY") # <-- 이 부분 수정
        self.elevenlabs_voice_id = self._get_secret("ELEVENLABS_VOICE_ID") # <-- 이 부분 수정 (새로 추가)
        self.news_api_key = self._get_secret("NEWS_API_KEY") # <-- 이 부분 수정
        self.pexels_api_key = self._get_secret("PEXELS_API_KEY") # <-- 이 부분 수정
        self.youtube_client_id = self._get_secret("YOUTUBE_CLIENT_ID") # <-- 이 부분 수정
        self.youtube_client_secret = self._get_secret("YOUTUBE_CLIENT_SECRET") # <-- 이 부분 수정
        self.youtube_refresh_token = self._get_secret("YOUTUBE_REFRESH_TOKEN") # <-- 이 부분 수정

        # OpenAI 및 Gemini API 키 로드 (이름 일치 확인)
        self.openai_keys_json = json.loads(self._get_secret("OPENAI_KEYS_JSON", is_json=True)) # <-- 이 부분 수정
        self.gemini_api_key = self._get_secret("GEMINI_API_KEY") # <-- 이 부분 수정

        # 비디오 생성 관련 설정
        self.daily_video_count = int(os.getenv("DAILY_VIDEO_COUNT", 5))
        self.target_video_duration_seconds = int(os.getenv("TARGET_VIDEO_DURATION_SECONDS", 50))

    # _get_secret 함수는 변경할 필요 없음
    def _get_secret(self, secret_name: str, is_json: bool = False):
        name = f"{self.secret_prefix}/{secret_name}/versions/latest"
        try:
            response = self.secret_client.access_secret_version(request={"name": name})
            secret_value = response.payload.data.decode("UTF-8")
            logger.info(f"Secret '{secret_name}' successfully loaded from Secret Manager.")
            if is_json:
                return json.loads(secret_value)
            return secret_value
        except Exception as e:
            logger.error(f"Secret '{secret_name}' 가져오기 실패: {e}", exc_info=True)
            raise ValueError(f"Secret '{secret_name}' could not be loaded. Please check Secret Manager and IAM permissions.")

# 전역 Config 인스턴스 생성
config = Config()
