import os
import json
import logging
from google.cloud import secretmanager

logger = logging.getLogger(__name__)

class Config:
    _gemini_keys = None
    _openai_keys = None

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
    def get_gemini_keys(cls) -> list[str]:
        if cls._gemini_keys is None:
            keys = os.getenv("GEMINI_API_KEYS")
            if not keys:
                keys = cls._get_secret_from_gcp("gemini-api-key")
            cls._gemini_keys = keys.split(",") if "," in keys else [keys]
            logger.info(f"Loaded {len(cls._gemini_keys)} Gemini API key(s).")
        return cls._gemini_keys

    @classmethod
    def get_openai_keys(cls) -> list[str]:
        if cls._openai_keys is None:
            keys_json = os.getenv("OPENAI_KEYS_JSON")
            if not keys_json:
                keys_json = cls._get_secret_from_gcp("openai-api-keys")
            try:
                # OPENAI_KEYS_JSON은 {'key1': 'sk-xxxx', 'key2': 'sk-yyyy'} 형태를 가정
                cls._openai_keys = list(json.loads(keys_json).values())
                logger.info(f"Loaded {len(cls._openai_keys)} OpenAI API key(s).")
            except json.JSONDecodeError as e:
                logger.error(f"OPENAI_KEYS_JSON 파싱 실패: {e}")
                raise ValueError("OPENAI_KEYS_JSON 형식이 올바르지 않습니다.")
        return cls._openai_keys

    @staticmethod
    def get_pexels_api_key() -> str:
        key = os.getenv("PEXELS_API_KEY")
        if not key:
            key = Config._get_secret_from_gcp("pexels-api-key")
        return key

    @staticmethod
    def get_elevenlabs_api_key() -> str:
        key = os.getenv("ELEVENLABS_API_KEY")
        if not key:
            key = Config._get_secret_from_gcp("elevenlabs-api-key")
        return key

    @staticmethod
    def get_elevenlabs_voice_id() -> str:
        voice_id = os.getenv("ELEVENLABS_VOICE_ID")
        if not voice_id:
            # GCP Secret Manager에 ELEVENLABS_VOICE_ID를 저장했다면 여기에서 가져오도록 수정 가능
            # 예: voice_id = Config._get_secret_from_gcp("elevenlabs-voice-id")
            # 하지만 대부분 voice_id는 고정값이므로 환경변수 또는 코드에 직접 명시해도 무방
            return "uyVNoMrnUku1dZyVEXwD" # 안나 킴 Voice ID (요청에 따라 고정)
        return voice_id

    @staticmethod
    def get_youtube_oauth_credentials() -> dict:
        creds_json = os.getenv("YOUTUBE_OAUTH_CREDENTIALS")
        if not creds_json:
            creds_json = Config._get_secret_from_gcp("youtube-oauth-credentials")
        try:
            return json.loads(creds_json)
        except json.JSONDecodeError as e:
            logger.error(f"YOUTUBE_OAUTH_CREDENTIALS 파싱 실패: {e}")
            raise ValueError("YOUTUBE_OAUTH_CREDENTIALS 형식이 올바르지 않습니다.")

    @staticmethod
    def get_gcp_project_id() -> str:
        project_id = os.getenv("GCP_PROJECT_ID")
        if not project_id:
            raise ValueError("GCP_PROJECT_ID 환경 변수가 설정되지 않았습니다.")
        return project_id
