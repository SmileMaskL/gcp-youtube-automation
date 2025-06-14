"""
YouTube 자동화 시스템 설정 (무조건 실행되는 버전)
"""
from pathlib import Path
import os

class Config:
    # 기본 디렉토리 설정
    BASE_DIR = Path(__file__).parent.parent
    TEMP_DIR = BASE_DIR / "temp"
    OUTPUT_DIR = BASE_DIR / "output"
    LOG_DIR = BASE_DIR / "logs"
    
    # 영상 설정
    SHORTS_WIDTH = 1080
    SHORTS_HEIGHT = 1920
    MAX_DURATION = 60  # 최대 영상 길이(초)
    
    # API 기본값
    DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # ElevenLabs 기본 음성
    
    @classmethod
    def ensure_directories(cls):
        """필요한 디렉토리 생성"""
        cls.TEMP_DIR.mkdir(exist_ok=True)
        cls.OUTPUT_DIR.mkdir(exist_ok=True)
        cls.LOG_DIR.mkdir(exist_ok=True)

# 초기화 시 디렉토리 생성
Config.ensure_directories()
