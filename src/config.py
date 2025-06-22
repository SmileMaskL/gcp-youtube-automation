# src/config.py (수정 및 보완된 전체 코드)

import os
from google.cloud import secretmanager
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Config:
    def __init__(self, project_id=None, bucket_name=None, env_vars=None):
        self.project_id = project_id if project_id else os.getenv("GCP_PROJECT_ID")
        self.bucket_name = bucket_name if bucket_name else os.getenv("GCP_BUCKET_NAME")
        
        if not self.project_id:
            logger.error("GCP_PROJECT_ID 환경 변수가 설정되지 않았습니다.")
            raise ValueError("GCP_PROJECT_ID 환경 변수를 설정해야 합니다.")
        
        self.secret_manager_client = secretmanager.SecretManagerServiceClient()
        self.project_path = f"projects/{self.project_id}"

        # ElevenLabs Voice ID는 환경 변수로 직접 설정 가능하도록
        self.elevenlabs_voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4FnGU8l8FGzN") # 기본값 설정

        # 추가적인 환경 변수 (예: WIF_PROVIDER, WIF_SERVICE_ACCOUNT는 GitHub Actions에서 사용)
        self.env_vars = env_vars if env_vars else {}
        self.load_env_vars() # 환경 변수 로드 함수 호출

    def load_env_vars(self):
        # GitHub Actions에서 설정된 환경 변수를 여기에서 가져올 수 있습니다.
        # 하지만 Secret Manager에서 직접 가져오는 것이 더 안전합니다.
        # 여기서는 예시로만 남겨둡니다.
        pass

    def _access_secret(self, secret_id):
        secret_name = f"{self.project_path}/secrets/{secret_id}/versions/latest"
        try:
            response = self.secret_manager_client.access_secret_version(request={"name": secret_name})
            payload = response.payload.data.decode("UTF-8")
            logger.info(f"Secret '{secret_id}' 로드 성공.")
            return payload
        except Exception as e:
            logger.error(f"Secret '{secret_id}' 로드 실패: {e}", exc_info=True)
            raise ValueError(f"Secret '{secret_id}'를 가져올 수 없습니다. 권한 및 존재 여부를 확인하세요.")

    def get_youtube_client_id(self):
        return self._access_secret("YOUTUBE_CLIENT_ID")

    def get_youtube_client_secret(self):
        return self._access_secret("YOUTUBE_CLIENT_SECRET")

    def get_youtube_refresh_token(self):
        return self._access_secret("YOUTUBE_REFRESH_TOKEN")
    
    def get_elevenlabs_api_key(self):
        # 환경 변수와 Secret Manager 중 선택하여 사용
        # self.elevenlabs_api_key는 이미 __init__에서 환경 변수로 초기화됨
        # Secret Manager에서 가져오려면 아래처럼 변경
        return self._access_secret("ELEVENLABS_API_KEY") 
        
    def get_openai_api_key(self):
        return self._access_secret("OPENAI_API_KEY")
    
    def get_gemini_api_key(self):
        return self._access_secret("GEMINI_API_KEY") # Gemini API 키 추가
    
    def get_newsapi_api_key(self):
        return self._access_secret("NEWSAPI_API_KEY") # NewsAPI 키 추가
        
    def get_pexels_api_key(self):
        # PexelsApi 모듈을 삭제했으므로, 이 키가 필요하다면 API 직접 호출 시 사용
        return self._access_secret("PEXELS_API_KEY") # Pexels API 키 추가
