import os
import json
from dotenv import load_dotenv

class Config:
    def __init__(self):
        # 로컬 개발 환경에서 .env 파일 로드
        # Cloud Run Jobs에서는 환경 변수가 자동으로 주입되므로 이 라인은 무시됩니다.
        load_dotenv() 

        # GCP 관련 설정
        self.GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
        self.GCP_BUCKET_NAME = os.getenv("GCP_BUCKET_NAME")

        # ElevenLabs API 설정
        self.ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
        self.ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "uyVNoMrnUku1dZyVEXwD") # 기본값: 안나 킴

        # Pexels API 설정
        self.PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

        # News API 설정
        self.NEWS_API_KEY = os.getenv("NEWS_API_KEY")

        # YouTube OAuth 2.0 자격 증명 (JSON 문자열 형태)
        # GitHub Secret에서 직접 주입됩니다.
        self.YOUTUBE_OAUTH_CREDENTIALS = os.getenv("YOUTUBE_OAUTH_CREDENTIALS")
        if not self.YOUTUBE_OAUTH_CREDENTIALS:
            print("Error: YOUTUBE_OAUTH_CREDENTIALS environment variable not set.")
            # 실제 배포 환경에서는 이 오류가 발생하면 안 됩니다.

        # AI API 키 설정 (JSON 문자열 형태)
        self.OPENAI_KEYS_JSON = os.getenv("OPENAI_KEYS_JSON")
        if self.OPENAI_KEYS_JSON:
            try:
                self.OPENAI_API_KEYS = json.loads(self.OPENAI_KEYS_JSON)
            except json.JSONDecodeError:
                print("Error: OPENAI_KEYS_JSON is not a valid JSON string.")
                self.OPENAI_API_KEYS = []
        else:
            self.OPENAI_API_KEYS = []
            
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        self.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") # 추가적인 Google API (ex: Search API 등) 사용 시

        # 로깅 및 모니터링
        self.LOG_FILE = "youtube_automation.log"
        self.TEMP_DIR = "output"
