# src/utils.py
# 이 파일은 동영상 제작에 필요한 모든 도구(AI, 음성, 영상 다운로드 등)를 모아놓은 곳입니다.

import os
import json
import logging
import uuid
import random
import requests
import re
from pathlib import Path
from moviepy.editor import VideoFileClip, ColorClip
from elevenlabs import Voice, VoiceSettings
from elevenlabs.client import ElevenLabs
from gtts import gTTS
from dotenv import load_dotenv
import google.generativeai as genai

# .env 파일에서 API 키를 불러옵니다.
load_dotenv()

# 프로그램 작동 기록(로그)을 남기기 위한 설정입니다.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("automation.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 영상 제작에 필요한 기본 설정값들을 모아놓은 곳입니다.
class Config:
    SHORTS_WIDTH = 1080
    SHORTS_HEIGHT = 1920
    TEMP_DIR = Path("temp")
    OUTPUT_DIR = Path("output")

    # temp, output 폴더가 없으면 자동으로 만들어줍니다.
    @classmethod
    def ensure_directories(cls):
        cls.TEMP_DIR.mkdir(exist_ok=True)
        cls.OUTPUT_DIR.mkdir(exist_ok=True)

# AI가 이상한 답변을 줘도 JSON 부분만 쏙 뽑아내는 함수입니다.
def clean_json_response(text: str) -> str:
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return match.group(0)
    logger.warning("응답에서 JSON 형식을 찾지 못했습니다. 원본 텍스트를 반환합니다.")
    return text

# ElevenLabs API가 고장났을 때, 대신 무료 구글 번역기 목소리로 음성을 만들어주는 함수입니다.
def create_default_audio(text: str, output_path: str) -> str:
    try:
        logger.info("gTTS를 사용하여 기본 음성을 생성합니다.")
        tts = gTTS(text=text, lang='ko', slow=False)
        tts.save(output_path)
        logger.info(f"gTTS 음성 저장 완료: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"gTTS 음성 생성 중 치명적 오류 발생: {e}")
        raise RuntimeError("모든 음성 생성 방법에 실패했습니다.")

# 텍스트를 AI 목소리로 바꿔주는 함수입니다.
def text_to_speech(text: str, output_path: str) -> str:
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
                voice_id="uyVNoMrnUku1dZyVEXwD",
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

# 배경 영상을 구하지 못했을 때, 대신 단순한 색깔 배경이라도 만들어주는 함수입니다.
def create_simple_video(duration=15) -> str:
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

# Pexels 사이트에서 주제에 맞는 무료 배경 영상을 다운로드하는 함수입니다.
def download_video_from_pexels(query: str, duration: int) -> str:
    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key:
        logger.warning("PEXELS_API_KEY가 없습니다. 기본 배경 영상을 사용합니다.")
        return create_simple_video(duration)
    
    try:
        logger.info(f"Pexels에서 '{query}' 관련 영상을 검색합니다.")
        headers = {"Authorization": api_key}
        search_query = query.split()[0] 
        url = f"https://api.pexels.com/videos/search?query={search_query}&per_page=10&orientation=portrait"
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        videos = response.json().get('videos', [])
        if not videos:
            raise ValueError("검색 결과에서 적합한 영상을 찾지 못했습니다.")
        
        selected_video_info = random.choice(videos)
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

# Gemini AI에게 영상 대본과 제목을 만들어달라고 요청하는 함수입니다.
def generate_viral_content(topic: str) -> dict:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY가 설정되지 않았습니다.")
        raise ValueError("Gemini API 키가 필요합니다.")
        
    try:
        logger.info("Gemini AI에게 콘텐츠 생성을 요청합니다.")
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        
        prompt = f"""
        당신은 최고의 유튜브 쇼츠 콘텐츠 제작자입니다. 다음 주제에 대해 시청자들이 끝까지 볼 수밖에 없는 바이럴 쇼츠 콘텐츠를 만들어주세요.
        규칙:
        1. 시청자의 시선을 사로잡는 강력한 제목 (25자 이내)
        2. 빠르고 간결하며 핵심만 담은 대본 (300자 내외)
        3. 영상과 관련된 인기 해시태그 3개 이상
        4. 절대 다른 말 하지 말고, 아래 JSON 형식만 반환할 것.

        ```json
        {{
          "title": "여기에 제목 작성",
          "script": "여기에 대본 작성",
          "hashtags": ["#해시태그1", "#해시태그2", "#해시태그3"]
        }}
        ```
        주제: {topic}
        """
        response = model.generate_content(prompt)
        cleaned_text = clean_json_response(response.text)
        content = json.loads(cleaned_text)
        
        if not all(key in content for key in ['title', 'script', 'hashtags']):
            raise ValueError("AI 응답에서 필수 필드(title, script, hashtags)가 누락되었습니다.")
        
        logger.info("Gemini AI 콘텐츠 생성 성공!")
        return content
    except Exception as e:
        logger.error(f"Gemini AI 콘텐츠 생성 실패: {e}. 기본 콘텐츠를 사용합니다.")
        return {
            "title": f"{topic}의 모든 것",
            "script": f"오늘은 {topic}에 대해 아무도 몰랐던 비밀을 알려드립니다! 끝까지 보시면 깜짝 놀랄 정보가 있습니다.",
            "hashtags": [f"#{topic.replace(' ', '')}", "#꿀팁", "#쇼츠"]
        }
