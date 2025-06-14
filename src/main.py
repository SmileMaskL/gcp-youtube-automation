"""
수익 최적화 유틸리티 (실전용 완벽 버전)
"""
import os
import re
import json
import uuid
import random
import logging
import requests
from pathlib import Path
from moviepy.editor import ColorClip, TextClip, CompositeVideoClip, AudioFileClip
from elevenlabs import Voice, VoiceSettings
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv
import google.generativeai as genai
from src.config import Config

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_simple_video(duration=60):
    """기본 배경 영상 생성 (수정된 버전)"""
    Config.ensure_directories()
    colors = [
        (26, 26, 26),    # 어두운 회색
        (42, 13, 13),    # 어두운 빨강
        (13, 42, 13),    # 어두운 초록
        (13, 13, 42)     # 어두운 파랑
    ]
    
    video_path = Config.TEMP_DIR / f"bg_{uuid.uuid4()}.mp4"
    clip = ColorClip(
        size=(Config.SHORTS_WIDTH, Config.SHORTS_HEIGHT),
        color=random.choice(colors),
        duration=duration
    )
    clip.write_videofile(str(video_path), fps=24, logger=None)
    return str(video_path)

def generate_viral_content_gemini(topic: str) -> dict:
    """Gemini를 사용하여 바이럴 콘텐츠 생성"""
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

def generate_tts_with_elevenlabs(text: str) -> str:
    """ElevenLabs TTS 음성 생성"""
    try:
        client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
        audio = client.generate(
            text=text,
            voice=Voice(
                voice_id=Config.DEFAULT_VOICE_ID,
                settings=VoiceSettings(stability=0.5, similarity_boost=0.75)
            ),
            model="eleven_multilingual_v2"
        )
        
        audio_path = Config.TEMP_DIR / f"audio_{uuid.uuid4()}.mp3"
        with open(audio_path, "wb") as f:
            for chunk in audio:
                f.write(chunk)
        return str(audio_path)
    except Exception as e:
        logger.error(f"TTS 생성 실패: {e}")
        raise

def download_video_from_pexels(query: str, duration: int) -> str:
    """Pexels에서 영상 다운로드"""
    try:
        headers = {"Authorization": os.getenv("PEXELS_API_KEY")}
        url = f"https://api.pexels.com/videos/search?query={query}&per_page=5"
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        videos = response.json().get('videos', [])
        if not videos:
            raise ValueError("동영상 없음")
            
        video = max(videos, key=lambda x: x.get('duration', 0))
        video_file = video['video_files'][0]['link']
        
        video_path = Config.TEMP_DIR / f"pexels_{uuid.uuid4()}.mp4"
        with requests.get(video_file, stream=True) as r:
            r.raise_for_status()
            with open(video_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return str(video_path)
    except Exception as e:
        logger.error(f"Pexels 실패: {e}")
        return create_simple_video(duration)

def create_shorts_video(video_path: str, audio_path: str, title: str) -> str:
    """최종 쇼츠 영상 생성"""
    try:
        video = VideoFileClip(video_path)
        audio = AudioFileClip(audio_path)
        
        # 영상 길이 조정
        if video.duration < audio.duration:
            video = video.loop(duration=audio.duration)
        else:
            video = video.subclip(0, audio.duration)
        
        # 텍스트 추가 (간단한 버전)
        txt_clip = TextClip(
            title[:50],  # 제목 처음 50자만 사용
            fontsize=40,
            color='white',
            size=(900, None),
            method='caption'
        ).set_position('center').set_duration(audio.duration)
        
        final = CompositeVideoClip([video, txt_clip]).set_audio(audio)
        output_path = Config.OUTPUT_DIR / f"final_{uuid.uuid4()}.mp4"
        final.write_videofile(str(output_path), fps=24, threads=4)
        return str(output_path)
    except Exception as e:
        logger.error(f"영상 생성 실패: {e}")
        raise

def cleanup_temp_files():
    """임시 파일 정리"""
    for file in Config.TEMP_DIR.glob("*"):
        try:
            file.unlink()
        except:
            pass
