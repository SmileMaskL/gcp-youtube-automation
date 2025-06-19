import os
import json
from google.cloud import secretmanager
from typing import List, Dict

class Config:
    @staticmethod
    def _get_secret(secret_name: str) -> str:
        try:
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{os.getenv('GCP_PROJECT_ID')}/secrets/{secret_name}/versions/latest"
            return client.access_secret_version(name=name).payload.data.decode('UTF-8')
        except Exception as e:
            raise RuntimeError(f"GCP Secret 접근 오류: {str(e)}")

    @classmethod
    def get_openai_keys(cls) -> List[str]:
        keys_json = cls._get_secret("openai-api-keys")
        return list(json.loads(keys_json).values()

    @classmethod
    def get_youtube_creds(cls) -> Dict:
        return json.loads(cls._get_secret("youtube-oauth-credentials"))
