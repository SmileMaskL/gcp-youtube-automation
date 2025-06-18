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
        os.makedirs(cls.TEMP_DIR, exist_ok=True)
        os.makedirs(cls.OUTPUT_DIR, exist_ok=True)
        os.makedirs(cls.LOG_DIR, exist_ok=True)

    @classmethod
    def get_api_key(cls, key_name: str) -> str:
        load_dotenv()
        if key_name not in os.environ:
            raise ValueError(f"환경변수 {key_name}가 설정되지 않았습니다")
        return os.environ[key_name]

# 클래스가 로드될 때 디렉토리 생성 실행
Config.ensure_directories()
