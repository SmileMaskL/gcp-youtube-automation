import os
from pathlib import Path
import logging

class Config:
    TEMP_DIR = Path("temp")
    OUTPUT_DIR = Path("output")
    SHORTS_WIDTH = 1080
    SHORTS_HEIGHT = 1920
    FONT_PATH = "fonts/Catfont.ttf"
    VIDEO_DURATION = 60
    ELEVENLABS_VOICE_ID = "uyVNoMrnUku1dZyVEXwD"
    
    @classmethod
    def initialize(cls):
        cls.TEMP_DIR.mkdir(parents=True, exist_ok=True)
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
    @staticmethod
    def get_api_key(key_name):
        key = os.getenv(key_name)
        if not key:
            raise ValueError(f"{key_name} 환경 변수가 설정되지 않았습니다.")
        return key

# 전역 설정 초기화
Config.initialize()
