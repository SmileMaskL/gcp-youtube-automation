# src/utils.py

import os
import json
import logging
import uuid
import random
import requests
import re
from pathlib import Path

# --- 필수 라이브러리 임포트 ---
from moviepy.editor import VideoFileClip, ColorClip
from elevenlabs import Voice, VoiceSettings
from elevenlabs.client import ElevenLabs
from gtts import gTTS
from dotenv import load_dotenv
import google.generativeai as genai

# --- 초기 설정 ---
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("automation.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- 설정값 클래스 ---
class Config:
    SHORTS_WIDTH = 1080
    SHORTS_HEIGHT = 1920
    TEMP_DIR = Path("temp")
    OUTPUT_DIR = Path("output")

    @classmethod
    def ensure_directories(cls):
        cls.TEMP_DIR.mkdir(exist_ok=True)
        cls.OUTPUT_DIR.mkdir(exist_ok=True)

# --- 함수 정의 ---
def clean_json_response(text: str) -> str:
    """AI의 응답에서 순수한 JSON 문자열만 추출합니다."""
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return match.group(0)
    logger.warning("응답에서 JSON 형식을 찾지 못했습니다. 원본 텍스트를 반환합니다.")
    return text

def create_default_audio(text: str, output_path: str) -> str:
    """ElevenLabs 실패 시 gTTS로 기본 음성을 생성합니다."""
    try:
        logger.info("gTTS를 사용하여 기본 음성을 생성합니다.")
        tts = gTTS(text=text, lang='ko', slow=False)
        tts.save(output_path)
        logger.info(f"gTTS 음성 저장 완료: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"gTTS 음성 생성 중 치명적 오류 발생: {e}")
        raise RuntimeError("모든 음성 생성 방법에 실패했습니다.")

def text_to_speech(text: str, output_path: str) -> str:
    """주어진 텍스트를 음성 파일로 변환합니다. ElevenLabs 우선, 실패 시 gTTS 사용."""
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        logger.warning("ElevenLabs API 키가 없습니다. gTTS를 사용합니다.")
        return create_default_audio(text, output_path)

    try:
        logger.info("ElevenLabs API를 사용하여 음성 생성을 시작합니다.")
        client = ElevenLabs(api_key=api_key)
        audio = client.generate(
            text=text,
            voice=Voice(
                voice_id="uyVNoMrnUku1dZyVEXwD", # 매력적인 여성 목소리 ID
                settings=VoiceSettings(stability=0.5, similarity_boost=0.75, style=0.1, use_speaker_boost=True)
            ),
            model="eleven_multilingual_v2"
        )
        with open(output_path, "wb") as f:
            for chunk in audio:
                if chunk:
                    f.write(chunk)
        logger.info(f"ElevenLabs 음성 저장 완료: {output_path}")
        return output_path
    except Exception as e:
        logger.warning(f"ElevenLabs API 실패: {e}. gTTS로 전환합니다.")
        return create_default_audio(text, output_path)

def create_simple_video(duration=15) -> str:
    """영상 다운로드 실패 시 사용할 간단한 색상 배경 영상을 생성합니다."""
    logger.info("기본 색상 배경 영상을 생성합니다.")
    colors = ["#1a1a1a", "#2a0d0d", "#0d1a14", "#0e0d2a"]
    video_path = Config.TEMP_DIR / f"default_bg_{uuid.uuid4()}.mp4"
    clip = ColorClip(
        size=(Config.SHORTS_WIDTH, Config.SHORTS_HEIGHT),
        color=random.choice(colors),
        duration=duration
    )
    clip.write_videofile(str(video_path), fps=24, logger=None)
    return str(video_path)

def download_video_from_pexels(query: str, duration: int) -> str:
    """Pexels에서 주제에 맞는 배경 영상을 다운로드합니다. 실패 시 기본 영상을 생성합니다."""
    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key:
        logger.warning("PEXELS_API_KEY가 없습니다. 기본 배경 영상을 사용합니다.")
        return create_simple_video(duration)
    
    try:
        logger.info(f"Pexels에서 '{query}' 관련 영상을 검색합니다.")
        headers = {"Authorization": api_key}
        # 좀 더 일반적인 검색을 위해 쿼리를 단순화할 수 있음
        search_query = query.split()[0] 
        url = f"https://api.pexels.com/videos/search?query={search_query}&per_page=10&orientation=portrait"
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        videos = response.json().get('videos', [])
        if not videos:
            raise ValueError("검색 결과에서 적합한 영상을 찾지 못했습니다.")
        
        # 다운로드할 영상 선택 (랜덤)
        selected_video_info = random.choice(videos)
        video_url = None
        for file_info in selected_video_info['video_files']:
            if file_info.get('quality') == 'hd' and file_info.get('width') == 1080:
                video_url = file_info['link']
                break
        if not video_url: # 적합한 화질이 없으면 아무거나
            video_url = selected_video_info['video_files'][0]['link']

        logger.info(f"다운로드할 영상 URL: {video_url}")
        video_path = Config.TEMP_DIR / f"pexels_{uuid.uuid4()}.mp4"
        with requests.get(video_url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(video_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        
        logger.info(f"Pexels 영상 다운로드 완료: {video_path}")
        return str(video_path)
    except Exception as e:
        logger.error(f"Pexels 영상 다운로드 실패: {e}. 기본 배경 영상을 사용합니다.")
        return create_simple_video(duration)

def generate_viral_content(topic: str) -> dict:
    """Gemini AI를 사용하여 유튜브 쇼츠 콘텐츠(제목, 대본, 해시태그)를 생성합니다."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY가 설정되지 않았습니다.")
        raise ValueError("Gemini API 키가 필요합니다.")
        
    try:
        logger.info("Gemini AI에게 콘텐츠 생성을 요청합니다.")
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash-latest') # 빠르고 효율적인 모델
        
        prompt = f"""
당신은 최고의 유튜브 쇼츠 콘텐츠 제작자입니다. 다음 주제에 대해 시청자들이 끝까지 볼 수밖에 없는 바이럴 쇼츠 콘텐츠를 만들어주세요.

**규칙:**
1. 시청자의 시선을 사로잡는 강력한 제목 (25자 이내)
2. 빠르고 간결하며 핵심만 담은 대본 (300자 내외)
3. 영상과 관련된 인기 해시태그 3개 이상
4. **절대 다른 말 하지 말고, 아래 JSON 형식만 반환할 것.**

```json
{{
  "title": "여기에 제목 작성",
  "script": "여기에 대본 작성",
  "hashtags": ["#해시태그1", "#해시태그2", "#해시태그3"]
}}
