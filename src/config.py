# src/config.py
import os
import json
from google.cloud import secretmanager

class Config:
    def __init__(self):
        self.project_id = os.environ.get('GCP_PROJECT_ID')
        self.bucket_name = os.environ.get('GCP_BUCKET_NAME')
        self.daily_video_count = 5 # 하루에 생성할 영상 수
        self.elevenlabs_voice_id = os.environ.get('ELEVENLABS_VOICE_ID', 'uyVNoMrnUku1dZyVEXwD') # 안나 킴 음성 ID

        # Secret Manager 클라이언트 초기화
        self.secret_client = secretmanager.SecretManagerServiceClient()

        # Secret Manager에서 API 키 로드
        self.elevenlabs_api_key = self._get_secret("ELEVENLABS_API_KEY")
        self.news_api_key = self._get_secret("NEWS_API_KEY")
        self.pexels_api_key = self._get_secret("PEXELS_API_KEY")
        
        # OpenAI 키는 로테이션을 위해 리스트로 로드
        openai_keys_json_str = self._get_secret("OPENAI_KEYS_B64s")
        self.openai_api_keys = json.loads(OPENAI_KEYS_B64s_str) if openai_keys_json_str else []
        
        self.gemini_api_key = self._get_secret("GEMINI_API_KEYy")
        
        self.youtube_client_id = self._get_secret("YOUTUBE_CLIENT_ID")
        self.youtube_client_secret = self._get_secret("YOUTUBE_CLIENT_SECRET")
        self.youtube_refresh_token = self._get_secret("YOUTUBE_REFRESH_TOKENn")

        # API 쿼터 관리 및 로깅 설정
        self.api_usage_tracking_bucket = self.bucket_name # 사용량 추적 정보를 저장할 버킷
        self.api_usage_tracking_file = "api_usage_log.json" # 사용량 추적 파일 이름

    def _get_secret(self, secret_name):
        """Secret Manager에서 Secret 값을 가져옵니다."""
        if not self.project_id:
            logger.error(f"GCP_PROJECT_ID 환경 변수가 설정되지 않았습니다. Secret '{secret_name}'를 가져올 수 없습니다.")
            return None
        
        name = f"projects/{self.project_id}/secrets/{secret_name}/versions/latest"
        try:
            response = self.secret_client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logger.error(f"Secret '{secret_name}' 가져오기 실패: {e}")
            return None

# 전역 설정 인스턴스
config = Config()

# 로깅 설정은 config.py가 import 될 때 한 번만 수행되도록
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
