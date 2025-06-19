import os
import json
import logging
from google.cloud import secretmanager
from typing import List, Dict

class Config:
    @staticmethod
    def _get_secret(secret_name: str) -> str:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{os.getenv('GCP_PROJECT_ID')}/secrets/{secret_name}/versions/latest"
        return client.access_secret_version(name=name).payload.data.decode('UTF-8')

    @classmethod
    def get_openai_keys(cls) -> List[str]:
        return list(json.loads(cls._get_secret("openai-api-keys")).values()

    @classmethod
    def get_pexels_key(cls) -> str:
        return cls._get_secret("pexels-api-key")

    @classmethod
    def get_youtube_creds(cls) -> Dict:
        return json.loads(cls._get_secret("youtube-oauth-credentials"))
