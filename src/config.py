import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
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
