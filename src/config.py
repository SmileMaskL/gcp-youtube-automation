# src/config.py
import os
import json
import logging
from google.cloud import secretmanager

logger = logging.getLogger(__name__)

class Config:
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.bucket_name = os.getenv("GCP_BUCKET_NAME")
        
        # GitHub Actions Secrets (환경 변수)에서 직접 읽거나, GCP Secret Manager에서 읽어올 경로 구성
        self.elevenlabs_api_key = self._get_secret("ELEVENLABS_API_KEY", "elevenlabs-api-key")
        self.elevenlabs_voice_id = self._get_secret("ELEVENLABS_VOICE_ID", "elevenlabs-voice-id", default_value="uyVNoMrnUku1dZyVEXwD") # 안나 킴 음성 ID
        self.news_api_key = self._get_secret("NEWS_API_KEY", "news-api-key")
        self.pexels_api_key = self._get_secret("PEXELS_API_KEY", "pexels-api-key")
        
        # OpenAI 키 로테이션을 위한 목록
        self.openai_api_keys = self._get_secret_json_list("OPENAI_KEYS_JSON", "openai-api-keys")
        
        self.gemini_api_key = self._get_secret("GEMINI_API_KEY", "gemini-api-key")

        self.youtube_client_id = self._get_secret("YOUTUBE_CLIENT_ID", "youtube-client-id")
        self.youtube_client_secret = self._get_secret("YOUTUBE_CLIENT_SECRET", "youtube-client-secret")
        self.youtube_refresh_token = self._get_secret("YOUTUBE_REFRESH_TOKEN", "youtube-refresh-token")

        self.font_path = os.path.join("fonts", "Catfont.ttf") # 고양이체 폰트 경로
        self.daily_video_count = 5 # 하루 5개 영상 제작 목표

        self.target_regions = ["us-central1"] # GCP 리전 고정
        self.current_region_index = 0 # 리전 로테이션 인덱스 (현재는 us-central1만 사용)

        # Cloud Logging 설정 (main.py에서 별도로 설정할 예정)
        
    def _get_secret(self, env_var_name: str, secret_name: str, default_value: str = None):
        """
        환경 변수에서 시크릿을 먼저 시도하고, 없으면 GCP Secret Manager에서 가져옵니다.
        """
        value = os.getenv(env_var_name)
        if value:
            logger.info(f"Loaded {env_var_name} from environment variable.")
            return value
        
        if self.project_id:
            try:
                client = secretmanager.SecretManagerServiceClient()
                name = f"projects/{self.project_id}/secrets/{secret_name}/versions/latest"
                response = client.access_secret_version(request={"name": name})
                secret_value = response.payload.data.decode("UTF-8")
                logger.info(f"Loaded {secret_name} from Secret Manager.")
                return secret_value
            except Exception as e:
                logger.warning(f"Failed to load secret '{secret_name}' from Secret Manager: {e}")
        
        if default_value:
            logger.info(f"Using default value for {env_var_name}.")
            return default_value
        
        logger.error(f"Secret '{env_var_name}' or '{secret_name}' not found in environment or Secret Manager.")
        raise ValueError(f"Required secret '{env_var_name}' or '{secret_name}' is missing.")

    def _get_secret_json_list(self, env_var_name: str, secret_name: str):
        """
        환경 변수 또는 Secret Manager에서 JSON 형식의 리스트 시크릿을 가져옵니다.
        """
        value = os.getenv(env_var_name)
        if value:
            try:
                keys = json.loads(value)
                if not isinstance(keys, list):
                    raise ValueError(f"Environment variable {env_var_name} is not a JSON list.")
                logger.info(f"Loaded {env_var_name} (JSON list) from environment variable.")
                return keys
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON from environment variable {env_var_name}: {e}")
                raise
        
        if self.project_id:
            try:
                client = secretmanager.SecretManagerServiceClient()
                name = f"projects/{self.project_id}/secrets/{secret_name}/versions/latest"
                response = client.access_secret_version(request={"name": name})
                secret_value = response.payload.data.decode("UTF-8")
                keys = json.loads(secret_value)
                if not isinstance(keys, list):
                    raise ValueError(f"Secret Manager secret {secret_name} is not a JSON list.")
                logger.info(f"Loaded {secret_name} (JSON list) from Secret Manager.")
                return keys
            except Exception as e:
                logger.warning(f"Failed to load JSON list secret '{secret_name}' from Secret Manager: {e}")
        
        logger.error(f"JSON list secret '{env_var_name}' or '{secret_name}' not found.")
        raise ValueError(f"Required JSON list secret '{env_var_name}' or '{secret_name}' is missing.")

    def get_next_region(self):
        """현재는 us-central1만 지원"""
        return self.target_regions[0]

# 전역 설정 인스턴스 (한 번만 로드)
config = Config()
