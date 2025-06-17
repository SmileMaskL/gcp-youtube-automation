import os
from pathlib import Path
import logging

class Config:
    # 디렉토리 설정
    TEMP_DIR = Path("temp")
    OUTPUT_DIR = Path("output")
    LOGS_DIR = Path("logs")
    
    # 영상 설정
    SHORTS_WIDTH = 1080
    SHORTS_HEIGHT = 1920
    VIDEO_DURATION = 60  # 60초 영상
    
    # 폰트 설정
    FONT_PATH = Path("fonts/Catfont.ttf")
    
    # API 설정
    ELEVENLABS_VOICE_ID = "uyVNoMrnUku1dZyVEXwD"
    
    @classmethod
    def initialize(cls):
        """필요한 디렉토리 생성 및 초기화"""
        cls.TEMP_DIR.mkdir(parents=True, exist_ok=True)
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        
    @staticmethod
    def get_api_key(key_name):
        """환경 변수에서 API 키 가져오기"""
        key = os.getenv(key_name)
        if not key:
            raise ValueError(f"{key_name} 환경 변수가 설정되지 않았습니다")
        return key

# 초기화 실행
Config.initialize()
