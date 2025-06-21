# src/config.py
import os
import json
import logging
from google.cloud import secretmanager

logger = logging.getLogger(__name__)

# 로깅 설정: 이 줄을 파일 상단에 추가하여 logger가 정의되도록 합니다.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Config:
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.bucket_name = os.getenv("GCP_BUCKET_NAME")
        self.region = os.getenv("REGION", "us-central1") # Cloud Function 배포 리전

        # Secret Manager 클라이언트 초기화
        try:
            self.secret_client = secretmanager.SecretManagerServiceClient()
            logger.info("Secret Manager client initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize Secret Manager client: {e}", exc_info=True)
            raise # 클라이언트 초기화 실패는 치명적이므로 예외 발생

        # 환경 변수에서 Secret Manager 경로 설정 (선택 사항)
        self.secret_prefix = f"projects/{self.project_id}/secrets" if self.project_id else "projects/YOUR_PROJECT_ID/secrets"

        # Secret Manager에서 API 키 로드
        # 중요: 아래 문자열은 Google Cloud Secret Manager에 저장된 시크릿의 '정확한 이름'과 일치해야 합니다.
        # 사용자분께서 제공한 secret 키 목록(대문자)에 따라 이름을 수정합니다.
        self.elevenlabs_api_key = self._get_secret("ELEVENLABS_API_KEY")
        self.elevenlabs_voice_id = self._get_secret("ELEVENLABS_VOICE_ID") # 추가된 Secret
        self.news_api_key = self._get_secret("NEWS_API_KEY")
        self.pexels_api_key = self._get_secret("PEXELS_API_KEY")
        self.youtube_client_id = self._get_secret("YOUTUBE_CLIENT_ID")
        self.youtube_client_secret = self._get_secret("YOUTUBE_CLIENT_SECRET")
        self.youtube_refresh_token = self._get_secret("YOUTUBE_REFRESH_TOKEN")
        
        # OpenAI 및 Gemini API 키는 로테이션을 위해 JSON 형태로 저장될 수 있습니다.
        # 따라서 이를 로드하여 파싱합니다.
        self.openai_keys_json = json.loads(self._get_secret("OPENAI_KEYS_JSON", is_json=True))
        self.gemini_api_key = self._get_secret("GEMINI_API_KEY")
        
        # NOTE: GCP_SERVICE_ACCOUNT_KEY, GOOGLE_API_KEY, GOOGLE_APPLICATION_CREDENTIALS
        # 이들은 일반적으로 직접 Secret Manager에서 로드하지 않고
        # Workload Identity Federation 또는 Cloud Functions의 기본 서비스 계정을 통해 자동으로 처리됩니다.
        # 따라서 Config 클래스에서 이들을 _get_secret으로 호출할 필요는 없습니다.

        # 비디오 생성 관련 설정
        self.daily_video_count = int(os.getenv("DAILY_VIDEO_COUNT", 5)) # 하루에 생성할 영상 수
        self.target_video_duration_seconds = int(os.getenv("TARGET_VIDEO_DURATION_SECONDS", 50)) # 숏츠 길이 (50초 권장)

    def _get_secret(self, secret_name: str, is_json: bool = False):
        """Secret Manager에서 시크릿 값을 가져옵니다."""
        # 시크릿 버전 경로 생성
        # `projects/PROJECT_NUMBER/secrets/SECRET_NAME/versions/latest` 형태여야 합니다.
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
            # 시크릿을 가져오지 못하면 애플리케이션 실행에 문제가 생기므로 예외를 다시 발생시킵니다.
            raise ValueError(f"Secret '{secret_name}' could not be loaded. Please check Secret Manager and IAM permissions.")

# 전역 Config 인스턴스 생성
config = Config()
