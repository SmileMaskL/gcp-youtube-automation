# src/config.py

import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
# 이 파일이 있는 위치의 상위 폴더(루트)에서 .env를 찾습니다.
dotenv_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

class Config:
    BASE_DIR = Path(__file__).parent.parent
    TEMP_DIR = BASE_DIR / "temp"
    OUTPUT_DIR = BASE_DIR / "output"
    LOG_DIR = BASE_DIR / "logs"
    FONTS_DIR = BASE_DIR / "fonts"
    FONT_PATH = FONTS_DIR / "Catfont.ttf"
    
    SHORTS_WIDTH = 1080
    SHORTS_HEIGHT = 1920
    MAX_DURATION = 59
    
    # ★★★ Gemini 모델 최신 버전으로 수정 ★★★
    AI_MODEL = "gemini-1.5-flash-latest"
    ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
    
    @classmethod
    def ensure_directories(cls):
        """필요한 디렉토리들이 존재하는지 확인하고 없으면 생성합니다."""
        cls.TEMP_DIR.mkdir(exist_ok=True, parents=True)
        cls.OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
        cls.LOG_DIR.mkdir(exist_ok=True, parents=True)

    @staticmethod
    def get_api_key(key_name):
        """환경 변수에서 API 키를 안전하게 가져옵니다."""
        key = os.getenv(key_name)
        if not key:
            raise ValueError(f"환경 변수 '{key_name}'가 설정되지 않았습니다. .env 파일을 확인해주세요.")
        return key

# 클래스가 로드될 때 디렉토리 생성 실행
Config.ensure_directories()
