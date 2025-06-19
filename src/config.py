import os
import json
import logging
from google.cloud import secretmanager
from typing import List, Dict

logging.basicConfig(level=logging.INFO)

class Config:
    @staticmethod
    def _get_secret(secret_name: str) -> str:
        try:
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{os.getenv('GCP_PROJECT_ID')}/secrets/{secret_name}/versions/latest"
            response = client.access_secret_version(name=name)
            return response.payload.data.decode('UTF-8')
        except Exception as e:
            logging.error(f"GCP Secret 접근 오류: {str(e)}")
            raise

    @classmethod
    def get_openai_keys(cls) -> List[str]:
        keys_json = cls._get_secret("openai-api-keys")
        try:
            keys = json.loads(keys_json)
            if isinstance(keys, dict):
                return keys.get('keys', [])
            return keys if isinstance(keys, list) else []
        except json.JSONDecodeError:
            return keys_json.split(',') if keys_json else []

    @classmethod
    def get_gemini_key(cls) -> str:
        return cls._get_secret("gemini-api-key")

    @classmethod
    def get_youtube_creds(cls) -> Dict:
        return json.loads(cls._get_secret("youtube-oauth-credentials"))

    @classmethod
    def get_elevenlabs_key(cls) -> str:
        return cls._get_secret("elevenlabs-api-key")

    @classmethod
    def get_pexels_key(cls) -> str:
        return cls._get_secret("pexels-api-key")
