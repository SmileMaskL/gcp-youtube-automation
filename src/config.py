import os
import json
import logging
from google.cloud import secretmanager

logger = logging.getLogger(__name__)

class Config:
    _gemini_keys = None
    _openai_keys = None
    _pexels_api_key = None
    _elevenlabs_api_key = None
    _elevenlabs_voice_id = None # 직접 설정하므로 Secret Manager에서 가져오지 않음
    _youtube_oauth_credentials = None
    _news_api_key = None

    @staticmethod
    def _get_secret_from_gcp(secret_name: str) -> str:
        try:
            client = secretmanager.SecretManagerServiceClient()
            # GCP_PROJECT_ID는 환경 변수에서 가져옵니다 (GitHub Secrets에서 설정).
            project_id = os.getenv("GCP_PROJECT_ID")
            if not project_id:
                raise ValueError("GCP_PROJECT_ID 환경 변수가 설정되지 않았습니다.")
            
            name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
            response = client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logger.error(f"GCP Secret Manager에서 '{secret_name}' 가져오기 실패: {e}")
            raise

    @classmethod
    def get_gemini_keys(cls) -> list[str]:
        if cls._gemini_keys is None:
            # GCP Secret Manager에서만 가져오도록 변경
            keys = cls._get_secret_from_gcp("gemini-api-key")
            cls._gemini_keys = keys.split(",") if "," in keys else [keys]
            logger.info(f"Loaded {len(cls._gemini_keys)} Gemini API key(s) from Secret Manager.")
        return cls._gemini_keys

    @classmethod
    def get_openai_keys(cls) -> list[str]:
        if cls._openai_keys is None:
            # GCP Secret Manager에서만 가져오도록 변경
            keys_json = cls._get_secret_from_gcp("openai-api-keys")
            try:
                cls._openai_keys = list(json.loads(keys_json).values())
                logger.info(f"Loaded {len(cls._openai_keys)} OpenAI API key(s) from Secret Manager.")
            except json.JSONDecodeError as e:
                logger.error(f"OPENAI_KEYS_JSON 파싱 실패: {e}")
                raise ValueError("OPENAI_KEYS_JSON 형식이 올바르지 않습니다.")
        return cls._openai_keys

    @classmethod
    def get_pexels_api_key(cls) -> str:
        if cls._pexels_api_key is None:
            cls._pexels_api_key = cls._get_secret_from_gcp("pexels-api-key")
            logger.info("Pexels API key loaded from Secret Manager.")
        return cls._pexels_api_key

    @classmethod
    def get_elevenlabs_api_key(cls) -> str:
        if cls._elevenlabs_api_key is None:
            cls._elevenlabs_api_key = cls._get_secret_from_gcp("elevenlabs-api-key")
            logger.info("ElevenLabs API key loaded from Secret Manager.")
        return cls._elevenlabs_api_key

    @classmethod
    def get_elevenlabs_voice_id(cls) -> str:
        # Voice ID는 고정값이므로 Secret Manager에서 가져오지 않고 직접 반환
        if cls._elevenlabs_voice_id is None:
            cls._elevenlabs_voice_id = os.getenv("ELEVENLABS_VOICE_ID", "uyVNoMrnUku1dZyVEXwD") # 환경변수 우선, 없으면 기본값
            logger.info(f"ElevenLabs Voice ID loaded: {cls._elevenlabs_voice_id}")
        return cls._elevenlabs_voice_id

    @classmethod
    def get_youtube_oauth_credentials(cls) -> dict:
        if cls._youtube_oauth_credentials is None:
            # YOUTUBE_OAUTH_CREDENTIALS는 GitHub Secrets에서 직접 환경변수로 전달
            # Workload Identity Federation을 통해 Secret Manager에서 가져올 수도 있지만,
            # YouTube API는 OAuth Flow를 따르므로, 이 토큰은 GitHub Secrets에 직접 저장하는 것이 일반적입니다.
            creds_json = os.getenv("YOUTUBE_OAUTH_CREDENTIALS")
            if not creds_json:
                raise ValueError("YOUTUBE_OAUTH_CREDENTIALS 환경 변수가 설정되지 않았습니다.")
            try:
                cls._youtube_oauth_credentials = json.loads(creds_json)
                logger.info("YouTube OAuth Credentials loaded from environment.")
            except json.JSONDecodeError as e:
                logger.error(f"YOUTUBE_OAUTH_CREDENTIALS 파싱 실패: {e}")
                raise ValueError("YOUTUBE_OAUTH_CREDENTIALS 형식이 올바르지 않습니다.")
        return cls._youtube_oauth_credentials

    @classmethod
    def get_gcp_project_id(cls) -> str:
        project_id = os.getenv("GCP_PROJECT_ID")
        if not project_id:
            raise ValueError("GCP_PROJECT_ID 환경 변수가 설정되지 않았습니다.")
        return project_id

    @classmethod
    def get_gcp_bucket_name(cls) -> Optional[str]:
        # GCP_BUCKET_NAME도 환경 변수 또는 Secret Manager에서 가져올 수 있음
        bucket_name = os.getenv("GCP_BUCKET_NAME")
        if not bucket_name:
            try:
                bucket_name = cls._get_secret_from_gcp("gcp-bucket-name")
            except Exception:
                logger.warning("GCP_BUCKET_NAME 환경 변수 및 Secret Manager에 설정되지 않았습니다.")
                return None
        logger.info(f"GCP Bucket Name loaded: {bucket_name}")
        return bucket_name

    @classmethod
    def get_news_api_key(cls) -> Optional[str]:
        # NEWS_API_KEY도 환경 변수 또는 Secret Manager에서 가져올 수 있음
        news_api_key = os.getenv("NEWS_API_KEY")
        if not news_api_key:
            try:
                news_api_key = cls._get_secret_from_gcp("news-api-key")
            except Exception:
                logger.warning("NEWS_API_KEY 환경 변수 및 Secret Manager에 설정되지 않았습니다.")
                return None
        logger.info("News API Key loaded.")
        return news_api_key
