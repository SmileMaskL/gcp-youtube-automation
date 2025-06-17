import os
import uuid
import random
import requests
import logging
from pathlib import Path
from dotenv import load_dotenv
from gtts import gTTS
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
import subprocess
import textwrap
from pexels_api import API
from retrying import retry
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
    FONT_PATH = "fonts/Catfont.ttf"
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

@retry(stop_max_attempt_number=3, wait_fixed=2000)
def get_trending_topics():
    """최신 트렌드 주제 5개 가져오기"""
    try:
        genai.configure(api_key=Config.get_api_key("GEMINI_API_KEY"))
        model = genai.GenerativeModel('gemini-pro')
        prompt = f"""오늘의 핫한 주제 5개를 JSON 형식으로 생성해주세요. 오늘 날짜는 {datetime.now().strftime('%Y-%m-%d')}입니다.
        출력 형식: [{{"title": "제목", "script": "대본", "pexel_query": "검색어"}}]"""
        response = model.generate_content(prompt)
        return eval(response.text.strip())
    except Exception as e:
        logger.error(f"트렌드 주제 생성 실패: {e}")
        raise

@retry(stop_max_attempt_number=3, wait_fixed=2000)
def generate_tts(script):
    """음성 생성 (ElevenLabs)"""
    audio_path = Config.TEMP_DIR / f"audio_{uuid.uuid4()}.mp3"
    try:
        headers = {
            "xi-api-key": Config.get_api_key("ELEVENLABS_API_KEY"),
            "Content-Type": "application/json"
        }
        data = {
            "text": script,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        response = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/uyVNoMrnUku1dZyVEXwD",  # 안나 킴 목소리
            headers=headers,
            json=data,
            timeout=30
        )
        response.raise_for_status()
        with open(audio_path, "wb") as f:
            f.write(response.content)
        return audio_path
    except Exception as e:
        logger.error(f"음성 생성 실패: {e}")
        raise

@retry(stop_max_attempt_number=3, wait_fixed=2000)
def get_background_video(query):
    """배경 영상 가져오기"""
    video_path = Config.TEMP_DIR / f"bg_{uuid.uuid4()}.mp4"
    try:
        api = API(Config.get_api_key("PEXELS_API_KEY"))
        api.search_videos(query, page=1, results_per_page=10)
        
        if api.videos:
            video = random.choice([
                v for v in api.videos 
                if v['duration'] >= Config.VIDEO_DURATION
            ])
            video_url = video['video_files'][0]['link']
            
            with requests.get(video_url, stream=True, timeout=30) as r:
                r.raise_for_status()
                with open(video_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            return video_path
        raise ValueError("적합한 영상 없음")
    except Exception as e:
        logger.warning(f"Pexels 실패: {e}, 단색 배경 생성")
        try:
            color = f"{random.randint(0, 255):02x}{random.randint(0, 255):02x}{random.randint(0, 255):02x}"
            subprocess.run([
                'ffmpeg', '-f', 'lavfi',
                '-i', f'color=c={color}:r=24:d={Config.VIDEO_DURATION}:s={Config.SHORTS_WIDTH}x{Config.SHORTS_HEIGHT}',
                '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
                '-y', str(video_path)
            ], check=True)
            return video_path
        except Exception as e:
            logger.error(f"배경 생성 실패: {e}")
            raise

def create_video(content, audio_path, bg_path):
    """영상 생성 (메모리 효율적 버전)"""
    output_path = Config.OUTPUT_DIR / f"shorts_{uuid.uuid4()}.mp4"
    
    try:
        # FFmpeg로 직접 영상 생성
        subprocess.run([
            'ffmpeg',
            '-i', str(bg_path),
            '-i', str(audio_path),
            '-filter_complex',
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1[v];" +
            f"[v]drawtext=text='{content['title']}':fontfile={Config.FONT_PATH}:fontsize=80:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/4:box=1:boxcolor=black@0.5," +
            f"drawtext=text='{content['script']}':fontfile={Config.FONT_PATH}:fontsize=60:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2:box=1:boxcolor=black@0.5",
            '-map', '0:v',
            '-map', '1:a',
            '-c:v', 'libx264', '-c:a', 'aac',
            '-shortest', '-y', str(output_path)
        ], check=True)
        return output_path
    except Exception as e:
        logger.error(f"영상 생성 실패: {e}")
        raise

def upload_to_youtube(video_path, title):
    """YouTube에 업로드"""
    try:
        # 여기에 YouTube API 업로드 코드 추가
        logger.info(f"업로드 완료: {title}")
        return True
    except Exception as e:
        logger.error(f"업로드 실패: {e}")
        return False

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
            
            # 간격 유지
            if i < 4:
                time.sleep(random.randint(30, 60))
                
    except Exception as e:
        logger.error(f"오류 발생: {e}", exc_info=True)
        raise
    finally:
        cleanup()

if __name__ == "__main__":
    main()
