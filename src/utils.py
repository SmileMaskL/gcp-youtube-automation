"""
수익 최적화 유틸리티 (무조건 실행되는 버전)
"""
import os
import json
import logging
import uuid
import random
import requests
from pathlib import Path
from moviepy.editor import ColorClip, TextClip, CompositeVideoClip, AudioFileClip
from elevenlabs import Voice, VoiceSettings
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv
import google.generativeai as genai

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("automation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Config:
    SHORTS_WIDTH = 1080
    SHORTS_HEIGHT = 1920
    MAX_DURATION = 60
    MIN_DURATION = 15
    TEMP_DIR = Path("temp")

    @classmethod
    def ensure_temp_dir(cls):
        cls.TEMP_DIR.mkdir(exist_ok=True)

def create_default_audio(text: str, output_path: str) -> str:
    try:
        from gtts import gTTS
        output_path = Path(output_path)
        output_path.parent.mkdir(exist_ok=True)
        tts = gTTS(text=text, lang='ko', slow=False)
        tts.save(str(output_path))
        return str(output_path)
    except Exception as e:
        logger.error(f"gTTS 실패: {e}")
        raise RuntimeError("음성 생성 실패")

def text_to_speech(text: str, output_path: str) -> str:
    try:
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            logger.warning("ElevenLabs API 키 없음. gTTS 사용")
            return create_default_audio(text, output_path)

        client = ElevenLabs(api_key=api_key)
        audio = client.generate(
            text=text,
            voice=Voice(
                voice_id="uyVNoMrnUku1dZyVEXwD",
                settings=VoiceSettings(stability=0.5, similarity_boost=0.75)
            ),
            model="eleven_multilingual_v2"
        )

        output_path = Path(output_path)
        with open(output_path, "wb") as f:
            for chunk in audio:
                f.write(chunk)
        return str(output_path)
    except Exception as e:
        logger.warning(f"ElevenLabs 실패: {e}. gTTS 사용")
        return create_default_audio(text, output_path)

def create_simple_video(duration=60):
    Config.ensure_temp_dir()
    colors = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00"]
    video_path = Config.TEMP_DIR / f"{uuid.uuid4()}.mp4"
    clip = ColorClip(
        size=(Config.SHORTS_WIDTH, Config.SHORTS_HEIGHT),
        color=random.choice(colors),
        duration=duration
    )
    clip.write_videofile(str(video_path), fps=24, logger=None)
    return str(video_path)

def download_video_from_pexels(query: str) -> str:
    try:
        api_key = os.getenv("PEXELS_API_KEY")
        if not api_key:
            raise ValueError("PEXELS_API_KEY 없음")

        headers = {"Authorization": api_key}
        url = f"https://api.pexels.com/videos/search?query={query}&per_page=5"
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        videos = response.json().get('videos', [])
        if not videos:
            raise ValueError("동영상 없음")
            
        video = max(videos, key=lambda x: x.get('duration', 0))
        video_file = video['video_files'][0]['link']
        
        video_path = Config.TEMP_DIR / f"{uuid.uuid4()}.mp4"
        with requests.get(video_file, stream=True) as r:
            r.raise_for_status()
            with open(video_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return str(video_path)
    except Exception as e:
        logger.error(f"Pexels 실패: {e}")
        return create_simple_video()

def generate_viral_content(topic: str) -> dict:
    try:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""반드시 다음 JSON 형식으로 응답:
{{
  "title": "25자 이내 제목",
  "script": "300자 내외 대본",
  "hashtags": ["#태그1", "#태그2", "#태그3"]
}}

주제: {topic}에 대한 YouTube Shorts 콘텐츠 생성"""
        
        response = model.generate_content(prompt)
        content = json.loads(response.text)
        
        if not all(key in content for key in ['title', 'script', 'hashtags']):
            raise ValueError("필수 필드 누락")
            
        return content
    except Exception as e:
        logger.error(f"Gemini 실패: {e}")
        return {
            "title": f"{topic}의 비밀",
            "script": f"{topic}으로 수익 창출하는 방법을 알려드립니다!",
            "hashtags": [f"#{topic}", "#수익", "#쇼츠"]
        }
