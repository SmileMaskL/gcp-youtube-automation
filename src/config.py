import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    BASE_DIR = Path(__file__).parent.parent
    TEMP_DIR = BASE_DIR / "temp"
    OUTPUT_DIR = BASE_DIR / "output"
    LOG_DIR = BASE_DIR / "logs"
    FONT_PATH = BASE_DIR / "fonts" / "Catfont.ttf"
    
    SHORTS_WIDTH = 1080
    SHORTS_HEIGHT = 1920
    MAX_DURATION = 60
    
    ELEVENLABS_VOICE_ID = "uyVNoMrnUku1dZyVEXwD"
    AI_MODEL = "gemini-1.0-pro"
    
    @classmethod
    def ensure_directories(cls):
        cls.TEMP_DIR.mkdir(exist_ok=True)
        cls.OUTPUT_DIR.mkdir(exist_ok=True)
        cls.LOG_DIR.mkdir(exist_ok=True)

    @staticmethod
    def get_api_key(key_name):
        key = os.getenv(key_name)
        if not key:
            raise ValueError(f"{key_name} 환경 변수가 설정되지 않았습니다")
        return key

Config.ensure_directories()
