import os
import json
import logging
from google.cloud import secretmanager
from typing import List, Dict

logger = logging.getLogger(__name__)

class Config:
    @staticmethod
    def _get_secret_from_gcp(secret_name: str) -> str:
        try:
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{os.getenv('GCP_PROJECT_ID')}/secrets/{secret_name}/versions/latest"
            response = client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logger.error(f"GCP Secret Manager에서 '{secret_name}' 가져오기 실패: {e}")
            raise

    @classmethod
    def get_gemini_keys(cls) -> List[str]:
        keys = cls._get_secret_from_gcp("gemini-api-key")
        return [keys.strip()]

    @classmethod
    def get_openai_keys(cls) -> List[str]:
        keys_json = cls._get_secret_from_gcp("openai-api-keys")
        try:
            return list(json.loads(keys_json).values())
        except json.JSONDecodeError as e:
            logger.error(f"OPENAI_KEYS_JSON 파싱 실패: {e}")
            raise

    @classmethod
    def get_pexels_api_key(cls) -> str:
        return cls._get_secret_from_gcp("pexels-api-key")

    @classmethod
    def get_elevenlabs_api_key(cls) -> str:
        return cls._get_secret_from_gcp("elevenlabs-api-key")

    @classmethod
    def get_elevenlabs_voice_id(cls) -> str:
        return os.getenv("ELEVENLABS_VOICE_ID", "uyVNoMrnUku1dZyVEXwD")

    @classmethod
    def get_youtube_oauth_credentials(cls) -> Dict:
        creds_json = os.getenv("YOUTUBE_OAUTH_CREDENTIALS")
        if not creds_json:
            raise ValueError("YOUTUBE_OAUTH_CREDENTIALS 환경 변수 없음")
        try:
            return json.loads(creds_json)
        except json.JSONDecodeError as e:
            logger.error(f"YOUTUBE_OAUTH_CREDENTIALS 파싱 실패: {e}")
            raise

    @classmethod
    def get_gcp_project_id(cls) -> str:
        project_id = os.getenv("GCP_PROJECT_ID")
        if not project_id:
            raise ValueError("GCP_PROJECT_ID 환경 변수 없음")
        return project_id

    @classmethod
    def get_elevenlabs_api_key(cls) -> str:
        try:
            return cls._get_secret_from_gcp("elevenlabs-api-key")
        except Exception as e:
            logger.error(f"ELEVENLABS_API_KEY 가져오기 실패: {e}")
        return os.getenv("ELEVENLABS_API_KEY", "")
