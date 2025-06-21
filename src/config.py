# src/config.py (수정 제안)

import os
import json
import logging
from google.cloud import secretmanager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Config:
    def __init__(self):
        # 환경 변수 초기화 (__init__에서 바로 가져옴)
        self.gcp_project_id = os.getenv("GCP_PROJECT_ID")
        self.gcp_bucket_name = os.getenv("GCP_BUCKET_NAME")
        self.region = os.getenv("REGION", "us-central1")
        self.elevenlabs_voice_id = os.getenv("ELEVENLABS_VOICE_ID") # 이건 env vars로 받으니 그대로 둠

        if not self.gcp_project_id:
            logger.critical("FATAL: GCP_PROJECT_ID environment variable is not set. Cannot proceed.")
            raise ValueError("GCP_PROJECT_ID environment variable is required.")

        # Secret Manager에서 가져올 Secret 이름들을 정의 (초기화 시 실제 값은 None)
        # Secret Manager에서 가져올 시크릿의 이름들을 정의합니다.
        # 이 변수명들은 main.py에서 사용될 것이므로 일관성 있게 유지해야 합니다.
        # 실제 Secret Value는 get_secrets_from_secret_manager() 호출 시 로드됩니다.
        self.elevenlabs_api_key = None # 실제 값은 나중에 로드
        self.news_api_key = None
        self.pexels_api_key = None
        self.youtube_client_id = None
        self.youtube_client_secret = None
        self.youtube_refresh_token = None
        self.openai_keys_json = None
        self.gemini_api_key = None
        self.google_api_key = None # Google Custom Search API
        
        # main.py의 AIRotation 클래스에서 사용하는 Secret Name 변수들 (project_id 기반)
        # YOUR_GCP_PROJECT_NUMBER 대신 self.gcp_project_id를 사용하도록 변경
        # 이 변수들은 실제 Secret Manager에서 Secret Version을 가져올 때 사용됩니다.
        self.elevenlabs_api_key_secret_name = f"projects/{self.gcp_project_id}/secrets/ELEVENLABS_API_KEY/versions/latest"
        self.youtube_oauth_credentials_secret_name = f"projects/{self.gcp_project_id}/secrets/YOUTUBE_OAUTH_CREDENTIALS/versions/latest"
        self.openai_keys_json_path = f"projects/{self.gcp_project_id}/secrets/OPENAI_KEYS_JSON/versions/latest"
        self.gemini_api_key_secret_name = f"projects/{self.gcp_project_id}/secrets/GEMINI_API_KEY/versions/latest"
        self.google_api_key_secret_name = f"projects/{self.gcp_project_id}/secrets/GOOGLE_API_KEY/versions/latest"
        self.news_api_key_secret_name = f"projects/{self.gcp_project_id}/secrets/NEWS_API_KEY/versions/latest"
        self.pexels_api_key_secret_name = f"projects/{self.gcp_project_id}/secrets/PEXELS_API_KEY/versions/latest"

        # API 쿼터 관리 설정
        self.api_quota_per_day = 10  # 일일 최대 API 호출 횟수 (예시, 필요에 따라 조정)
        self.api_quota_per_month = 300 # 월간 최대 API 호출 횟수 (예시, 필요에 따라 조정)

        # (선택 사항) YouTube 업로드 관련 설정
        self.youtube_category_id = "22" # People & Blogs 카테고리
        self.youtube_privacy_status = "private" # "public", "private", "unlisted" 중 선택

        # Secret Manager Client는 필요할 때만 초기화하도록 변경
        self._secret_client = None

    def _get_secret_client(self):
        if self._secret_client is None:
            try:
                self._secret_client = secretmanager.SecretManagerServiceClient()
                logger.info("Secret Manager client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Secret Manager client: {e}", exc_info=True)
                raise # 클라이언트 초기화 실패는 치명적이므로 예외 발생
        return self._secret_client

    def get_secret_value(self, secret_full_path: str, is_json: bool = False):
        """Secret Manager에서 시크릿 값을 가져오는 일반적인 메서드"""
        secret_client = self._get_secret_client()
        logger.debug(f"Attempting to access secret: {secret_full_path}")
        try:
            response = secret_client.access_secret_version(request={"name": secret_full_path})
            secret_value = response.payload.data.decode("UTF-8")
            logger.info(f"Secret from path '{secret_full_path}' successfully loaded.")
            if is_json:
                return json.loads(secret_value)
            return secret_value
        except Exception as e:
            logger.error(f"Failed to fetch secret from '{secret_full_path}': {e}", exc_info=True)
            raise ValueError(f"Secret from '{secret_full_path}' could not be loaded. Please check Secret Manager and IAM permissions.")

    # main.py에서 이 메서드를 호출하여 필요한 모든 시크릿을 로드합니다.
    def load_secrets_into_config(self):
        """모든 필요한 시크릿을 Secret Manager에서 로드하여 config 객체에 할당합니다."""
        logger.info("Loading secrets from Secret Manager...")
        try:
            self.elevenlabs_api_key = self.get_secret_value(self.elevenlabs_api_key_secret_name)
            self.news_api_key = self.get_secret_value(self.news_api_key_secret_name)
            self.pexels_api_key = self.get_secret_value(self.pexels_api_key_secret_name)
            self.youtube_client_id = self.get_secret_value(f"projects/{self.gcp_project_id}/secrets/YOUTUBE_CLIENT_ID/versions/latest")
            self.youtube_client_secret = self.get_secret_value(f"projects/{self.gcp_project_id}/secrets/YOUTUBE_CLIENT_SECRET/versions/latest")
            self.youtube_refresh_token = self.get_secret_value(f"projects/{self.gcp_project_id}/secrets/YOUTUBE_REFRESH_TOKEN/versions/latest")
            self.openai_keys_json = json.loads(self.get_secret_value(self.openai_keys_json_path))
            self.gemini_api_key = self.get_secret_value(self.gemini_api_key_secret_name)
            self.google_api_key = self.get_secret_value(self.google_api_key_secret_name)

            # NOTE: youtube_oauth_credentials_secret_name은 실제 OAuth JSON 파일을 저장하는 Secret 이름입니다.
            # 이 Secret은 YouTubeUploader에서 직접 사용되므로, 여기서는 값으로 로드하지 않고 경로만 설정합니다.
            # 만약 YouTubeUploader에서 파일 경로가 아닌 직접 credential JSON 내용을 받는다면, 이 부분을 수정해야 합니다.
            # 현재 main.py에서 youtube_oauth_credentials_secret_name을 사용하므로, 그대로 유지합니다.
            
            logger.info("All secrets successfully loaded into config.")
        except Exception as e:
            logger.error(f"Failed to load one or more secrets: {e}")
            raise # 시크릿 로드 실패는 치명적이므로 예외 발생

# config 객체는 초기화 시 환경 변수만 로드하고, 시크릿은 나중에 로드합니다.
config = Config()
