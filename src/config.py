# src/config.py

import os
from google.cloud import secretmanager
import logging
import json

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

        self.elevenlabs_voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4FnGU8l8FGzN")

        self.env_vars = env_vars if env_vars else {}
        self.load_env_vars()

    def load_env_vars(self):
        pass

    def _access_secret(self, secret_id):
        """Secret Manager에서 특정 시크릿의 최신 버전을 가져옵니다."""
        secret_name = f"{self.project_path}/secrets/{secret_id}/versions/latest"
        try:
            response = self.secret_manager_client.access_secret_version(request={"name": secret_name})
            payload = response.payload.data.decode("UTF-8")
            logger.info(f"Secret '{secret_id}' 로드 성공.")
            return payload
        except Exception as e:
            logger.error(f"Secret '{secret_id}' 로드 실패: {e}", exc_info=True)
            # E501 해결: 줄 길이를 79자 이하로 맞춤
            raise ValueError(f"Secret '{secret_id}'를 가져올 수 없습니다. "
                             f"권한 및 존재 여부를 확인하세요.")

    def get_youtube_client_id(self):
        return self._access_secret("YOUTUBE_CLIENT_ID")

    def get_youtube_client_secret(self):
        return self._access_secret("YOUTUBE_CLIENT_SECRET")

    def get_youtube_refresh_token(self):
        return self._access_secret("YOUTUBE_REFRESH_TOKEN")

    def get_elevenlabs_api_key(self):
        return self._access_secret("ELEVENLABS_API_KEY")

    def get_openai_api_keys(self):
        """OPENAI_API_KEYS 시크릿에서 JSON 형태의 여러 OpenAI API 키를 가져옵니다."""
        keys_json_str = self._access_secret("OPENAI_API_KEYS")
        try:
            keys = json.loads(keys_json_str)
            if not isinstance(keys, list):
                raise TypeError("OPENAI_API_KEYS 시크릿은 JSON 배열 형태여야 합니다.")
            logger.info(f"OPENAI_API_KEYS에서 {len(keys)}개의 키 로드 완료.")
            return keys
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"OPENAI_API_KEYS 시크릿 파싱 실패: {e}", exc_info=True)
            # E501 해결: 줄 길이를 79자 이하로 맞춤
            raise ValueError("OPENAI_API_KEYS 시크릿 내용이 올바른 JSON 배열 형식이 아닙니다.")

    def get_gemini_api_key(self):
        return self._access_secret("GEMINI_API_KEY")

    def get_newsapi_api_key(self):
        return self._access_secret("NEWSAPI_API_KEY")

    def get_pexels_api_key(self):
        return self._access_secret("PEXELS_API_KEY")
    
