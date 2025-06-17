import os
from dotenv import load_dotenv

load_dotenv()

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

with open(os.getenv("YOUTUBE_CREDENTIALS_PATH")) as f:
    creds_json = json.load(f)

class Config:
    GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

    PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

    YT_CLIENT_ID = os.getenv("YT_CLIENT_ID")
    YT_CLIENT_SECRET = os.getenv("YT_CLIENT_SECRET")
    YT_REDIRECT_URI = os.getenv("YT_REDIRECT_URI")

    GCP_BUCKET_NAME = os.getenv("GCP_BUCKET_NAME")

    YOUTUBE_CREDENTIALS_PATH = os.getenv("YOUTUBE_CREDENTIALS_PATH")
    
    # 기본 디렉토리 설정
    BASE_DIR = Path(__file__).parent.parent
    TEMP_DIR = BASE_DIR / "temp"
    OUTPUT_DIR = BASE_DIR / "output"
    LOGS_DIR = BASE_DIR / "logs"
    FONT_PATH = BASE_DIR / "fonts" / "Catfont.ttf"
    
    # 영상 설정
    SHORTS_WIDTH = 1080
    SHORTS_HEIGHT = 1920
    VIDEO_DURATION = 60  # 60초
    
    # API 설정
    ELEVENLABS_VOICE_ID = "uyVNoMrnUku1dZyVEXwD"
    
    @classmethod
    def initialize(cls):
        """필요한 디렉토리 생성"""
        cls.TEMP_DIR.mkdir(exist_ok=True)
        cls.OUTPUT_DIR.mkdir(exist_ok=True)
        cls.LOGS_DIR.mkdir(exist_ok=True)
    
    @staticmethod
    def get_api_key(key_name):
        """환경 변수에서 API 키 가져오기"""
        key = os.getenv(key_name)
        if not key:
            raise ValueError(f"{key_name} 환경 변수가 설정되지 않았습니다")
        return key

# 초기화 실행
Config.initialize()
