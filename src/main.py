import os
import uuid
import random
import requests
import logging
from pathlib import Path
from dotenv import load_dotenv
import time
import shutil
from datetime import datetime
import json

# 로거 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('youtube_shorts.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

class Config:
    TEMP_DIR = Path("/tmp/youtube_temp")
    OUTPUT_DIR = Path("output")
    SHORTS_WIDTH = 1080
    SHORTS_HEIGHT = 1920
    FONT_PATH = "fonts/Catfont.ttf"  # 상대 경로로 변경
    VIDEO_DURATION = 60  # 60초 영상
    
    @staticmethod
    def get_api_key(key_name):
        key = os.getenv(key_name)
        if not key:
            raise ValueError(f"{key_name} 환경 변수가 설정되지 않았습니다.")
        return key

    @classmethod
    def initialize(cls):
        cls.TEMP_DIR.mkdir(parents=True, exist_ok=True)
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 다른 모듈에서 정의한 함수 임포트
from content_generator import get_trending_topics
from video_creator import create_video
from youtube_uploader import upload_to_youtube
from tts_generator import generate_tts
from bg_downloader import get_background_video

def cleanup():
    """임시 파일 정리"""
    try:
        shutil.rmtree(Config.TEMP_DIR, ignore_errors=True)
    except Exception as e:
        logger.warning(f"정리 실패: {e}")

def main():
    try:
        Config.initialize()
        topics = get_trending_topics()
        
        for i, topic in enumerate(topics[:5]):  # 상위 5개 주제만 처리
            logger.info(f"처리 중: {i+1}/5 - {topic['title']}")
            
            audio_path = generate_tts(topic["script"])
            bg_path = get_background_video(topic["pexel_query"])
            video_path = create_video(topic, audio_path, bg_path)
            
            if upload_to_youtube(video_path, topic["title"]):
                logger.info(f"성공: {video_path}")
            
            # 간격 유지 (API 과부하 방지)
            if i < 4:
                time.sleep(random.randint(30, 60))
                
    except Exception as e:
        logger.error(f"오류 발생: {e}", exc_info=True)
        raise
    finally:
        cleanup()

if __name__ == "__main__":
    main()
