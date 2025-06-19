import os
import json
from google.cloud import secretmanager

class Config:
    @staticmethod
    def get_gemini_keys():
        keys = os.getenv("GEMINI_API_KEYS")
        if not keys:
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{os.getenv('GCP_PROJECT_ID')}/secrets/gemini-api-key/versions/latest"
            response = client.access_secret_version(request={"name": name})
            keys = response.payload.data.decode("UTF-8")
        return keys.split(",") if "," in keys else [keys]

    @staticmethod
    def get_openai_keys():
        keys_json = os.getenv("OPENAI_KEYS_JSON")
        if not keys_json:
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{os.getenv('GCP_PROJECT_ID')}/secrets/openai-api-keys/versions/latest"
            response = client.access_secret_version(request={"name": name})
            keys_json = response.payload.data.decode("UTF-8")
        return list(json.loads(keys_json).values())
