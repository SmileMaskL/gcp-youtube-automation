import os
import logging
import json

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class Config:
    def __init__(self, project_id=None, bucket_name=None):
        # 환경 변수를 직접 읽어옵니다. Cloud Run이 Secret Manager의 값을 여기에 주입합니다.
        self.project_id = project_id if project_id else os.getenv("GCP_PROJECT_ID")
        self.bucket_name = bucket_name if bucket_name else os.getenv("GCP_BUCKET_NAME")

        if not self.project_id:
            logger.error("GCP_PROJECT_ID 환경 변수가 설정되지 않았습니다.")
            raise ValueError("GCP_PROJECT_ID 환경 변수를 설정해야 합니다.")
            
        # ElevenLabs Voice ID는 환경 변수에서 기본값을 제공합니다.
        self.elevenlabs_voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4FnGU8l8FGzN")

        # OpenAI API 키는 쉼표로 구분된 문자열로 환경 변수에 있을 것으로 예상합니다.
        # 이를 리스트로 변환합니다.
        openai_keys_str = os.getenv("OPENAI_API_KEYS", "")
        self._openai_api_keys = [key.strip() for key in openai_keys_str.split(',') if key.strip()]
        if not self._openai_api_keys:
            logger.warning("OPENAI_API_KEYS 환경 변수가 설정되지 않았거나 비어 있습니다.")

        # AI 모델 선택을 위한 기본값 (필요에 따라 변경)
        self.default_ai_model_content = os.getenv("DEFAULT_AI_MODEL_CONTENT", "gemini")  
        self.default_ai_model_summary = os.getenv("DEFAULT_AI_MODEL_SUMMARY", "openai")  

        # YouTube 관련 기본 설정
        self.youtube_category_id = os.getenv("YOUTUBE_CATEGORY_ID", "28") # 예: 뉴스 & 정치
        self.video_resolutions = {"shorts": (1080, 1920)} # 쇼츠 해상도
        self.max_video_duration_seconds = 59 # 쇼츠 최대 길이

        logger.info("Config 객체 초기화 완료. 환경 변수를 사용합니다.")

    # Secret Manager에서 직접 가져오는 대신, 이미 환경 변수로 주입된 값을 반환합니다.
    def get_youtube_client_id(self):
        return os.getenv("YOUTUBE_CLIENT_ID")

    def get_youtube_client_secret(self):
        return os.getenv("YOUTUBE_CLIENT_SECRET")

    def get_youtube_refresh_token(self):
        return os.getenv("YOUTUBE_REFRESH_TOKEN")

    def get_elevenlabs_api_key(self):
        return os.getenv("ELEVENLABS_API_KEY")

    def get_openai_api_keys(self):
        # 이미 __init__에서 처리했으므로 저장된 리스트 반환
        return self._openai_api_keys

    def get_gemini_api_key(self):
        return os.getenv("GEMINI_API_KEY")

    def get_newsapi_api_key(self):
        return os.getenv("NEWSAPI_API_KEY")

    def get_pexels_api_key(self):
        return os.getenv("PEXELS_API_KEY")

    def get_elevenlabs_voice_id(self):
        # 이미 __init__에서 환경 변수 기본값과 함께 로드
        return self.elevenlabs_voice_id

# ★ 이 부분이 핵심입니다! ★
# Config 클래스의 인스턴스를 생성하여 'settings'라는 이름으로 export 합니다.
settings = Config()
