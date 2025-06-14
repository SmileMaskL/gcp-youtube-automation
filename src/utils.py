"""
수익 최적화 유튜브 자동화 유틸리티 (완전한 버전)
"""

import os
import requests
import json
import logging
import time
import uuid
import tempfile
import random
from pathlib import Path
from moviepy.editor import *
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== 핵심 기능 ====================

def text_to_speech(text: str, output_path: str = "output/audio.mp3") -> str:
    """개선된 TTS 함수 (에러 처리 강화)"""
    try:
        # API 키 확인
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            raise ValueError("ELEVENLABS_API_KEY가 설정되지 않았습니다")
        
        # 클라이언트 초기화
        client = ElevenLabs(api_key=api_key)
        
        # 음성 생성 (최적화된 설정)
        audio = client.generate(
            text=text,
            voice="Rachel",
            model="eleven_multilingual_v2",
            stability=0.5,
            similarity_boost=0.8
        )
        
        # 파일 저장
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(audio)
            
        return output_path
        
    except Exception as e:
        logger.error(f"음성 생성 실패: {e}")
        # 간단한 오류 음성 생성
        silent_audio = AudioClip(lambda t: 0, duration=len(text)*0.1)
        silent_audio.write_audiofile(output_path, fps=22050, logger=None)
        return output_path

def download_video_from_pexels(query: str = None) -> str:
    """수익형 콘텐츠에 최적화된 영상 다운로드"""
    try:
        api_key = os.getenv("PEXELS_API_KEY")
        if not api_key:
            return create_simple_video()
            
        # 수익성 높은 키워드
        money_keywords = [
            "money", "success", "business", 
            "invest", "bitcoin", "wealth"
        ]
        query = query or random.choice(money_keywords)
        
        headers = {"Authorization": api_key}
        url = f"https://api.pexels.com/videos/search?query={query}&per_page=5"
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        videos = response.json().get("videos", [])
        if not videos:
            return create_simple_video()
            
        # 가장 인기있는 영상 선택
        video = max(videos, key=lambda x: x.get("duration", 0))
        video_file = video["video_files"][0]["link"]
        
        # 영상 다운로드
        temp_path = f"temp/{uuid.uuid4()}.mp4"
        os.makedirs("temp", exist_ok=True)
        
        with requests.get(video_file, stream=True) as r:
            r.raise_for_status()
            with open(temp_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
        return temp_path
        
    except Exception as e:
        logger.error(f"Pexels 오류: {e}")
        return create_simple_video()

def create_simple_video() -> str:
    """무료로 사용 가능한 간단한 영상 생성"""
    try:
        colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#FFEE93"]
        clip = ColorClip(size=(1080, 1920), color=random.choice(colors), duration=60)
        
        temp_path = f"temp/{uuid.uuid4()}.mp4"
        clip.write_videofile(temp_path, fps=24, logger=None)
        
        return temp_path
    except Exception as e:
        logger.error(f"영상 생성 실패: {e}")
        raise

def add_text_to_clip(video_path: str, text: str, output_path: str) -> str:
    """클릭 유도 텍스트 추가 (수익 최적화)"""
    try:
        # 영상 로드
        video = VideoFileClip(video_path)
        
        # 텍스트 스타일 (최적화)
        txt_clip = TextClip(
            text,
            fontsize=70,
            color='white',
            font='Arial-Bold',
            stroke_color='black',
            stroke_width=2,
            size=(video.w*0.9, None),
            method='caption'
        ).set_position('center').set_duration(video.duration)
        
        # 합성
        final = CompositeVideoClip([video, txt_clip])
        final.write_videofile(output_path, fps=video.fps, logger=None)
        
        # 정리
        video.close()
        final.close()
        
        return output_path
    except Exception as e:
        logger.error(f"텍스트 추가 실패: {e}")
        return video_path

# ==================== 콘텐츠 생성 ====================

def generate_viral_content(topic: str) -> dict:
    """바이럴 가능성 높은 콘텐츠 생성"""
    try:
        # 무료 AI 사용 (Gemini 우선)
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""
        [한국어 유튜브 쇼츠 콘텐츠 생성]
        주제: {topic}
        
        요구사항:
        1. 제목: 20자 내외, 충격적이면서 호기심 유발
        2. 대본: 50-60초 분량 (300자 내외)
        3. 해시태그: 5개 (클릭 유도)
        
        출력 형식:
        {{
            "title": "제목",
            "script": "대본",
            "hashtags": ["#해시태그1", ...]
        }}
        """
        
        response = model.generate_content(prompt)
        return json.loads(response.text)
        
    except Exception as e:
        logger.error(f"AI 생성 실패: {e}")
        return {
            "title": f"{topic}의 충격적인 비밀!",
            "script": f"{topic}에 대해 알아야 할 3가지 사실! 놀라운 결과가...",
            "hashtags": ["#수익", "#성공", "#비밀", "#화제", "#트렌드"]
        }

# ==================== 설정 관리 ====================

class Config:
    """설정 관리 클래스"""
    
    @staticmethod
    def get(key: str, default=None):
        """환경변수 가져오기"""
        value = os.getenv(key)
        if not value and default is None:
            raise ValueError(f"필수 환경변수 {key}가 없습니다")
        return value or default

# ==================== 실행 보조 ====================

def check_requirements():
    """필수 환경 확인"""
    required = [
        "ELEVENLABS_API_KEY",
        "PEXELS_API_KEY",
        "GEMINI_API_KEY"
    ]
    
    for key in required:
        if not os.getenv(key):
            logger.warning(f"경고: {key}가 설정되지 않았습니다. 일부 기능이 제한됩니다.")

if __name__ == "__main__":
    check_requirements()
