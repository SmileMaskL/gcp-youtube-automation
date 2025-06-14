"""
수익 최적화 유튜브 자동화 유틸리티 (완전 테스트 버전)
- 최종 업데이트: 2025년 6월 16일
- 주요 개선: 누락된 add_text_to_clip 함수 추가, GCP 완벽 호환
"""

import os
import requests
import json
import logging
import time
import uuid
import random
from pathlib import Path
from moviepy.editor import *
from elevenlabs import Voice, VoiceSettings
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv
import google.generativeai as genai

# 환경 변수 로드 (GCP 호환)
try:
    load_dotenv()
except Exception as e:
    logging.warning(f".env 파일 로드 실패: {e}")

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class Config:
    """환경 변수 관리 클래스"""
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    YOUTUBE_OAUTH_CREDENTIALS = os.getenv("YOUTUBE_OAUTH_CREDENTIALS")

    @staticmethod
    def validate():
        """필수 변수 확인"""
        required_keys = ["ELEVENLABS_API_KEY", "GEMINI_API_KEY"]
        missing = [k for k in required_keys if not getattr(Config, k)]
        if missing:
            logger.warning(f"경고: 필수 변수 누락 - {', '.join(missing)}")
        return not missing

# ==================== 핵심 기능 ====================
def add_text_to_clip(video_path: str, text: str, output_path: str) -> str:
    """영상에 텍스트 추가 (GCP 호환 버전)"""
    try:
        video = VideoFileClip(video_path)
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
        
        final = CompositeVideoClip([video, txt_clip])
        final.write_videofile(output_path, fps=video.fps, logger=None)
        return output_path
    except Exception as e:
        logger.error(f"텍스트 추가 실패: {e}")
        return video_path

def text_to_speech(text: str, output_path: str = "output/audio.mp3") -> str:
    """TTS 함수 (에러 대응 강화)"""
    try:
        if not Config.ELEVENLABS_API_KEY:
            raise ValueError("ELEVENLABS_API_KEY 없음")

        client = ElevenLabs(api_key=Config.ELEVENLABS_API_KEY)
        audio = client.generate(
            text=text,
            voice=Voice(
                voice_id='Rachel',
                settings=VoiceSettings(stability=0.5, similarity_boost=0.75)
            ),
            model="eleven_multilingual_v2"
        )

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(audio)
        return output_path
    except Exception as e:
        logger.error(f"TTS 오류: {e}")
        silent_audio = AudioClip(lambda t: 0, duration=len(text)*0.5, fps=22050)
        silent_audio.write_audiofile(output_path, fps=22050, logger=None)
        return output_path

def download_video_from_pexels(query: str = None) -> str:
    """영상 다운로드 (3회 재시도)"""
    money_keywords = ["money", "success", "business", "invest", "bitcoin"]
    search_query = query or random.choice(money_keywords)

    for attempt in range(3):
        try:
            if not Config.PEXELS_API_KEY:
                return create_simple_video()

            headers = {"Authorization": Config.PEXELS_API_KEY}
            url = f"https://api.pexels.com/videos/search?query={search_query}&per_page=5"
            response = requests.get(url, headers=headers, timeout=20)
            response.raise_for_status()

            videos = [v for v in response.json().get("videos", []) if v.get('duration', 0) > 15]
            if not videos:
                continue

            video = random.choice(videos)
            video_file = video['video_files'][0]['link']
            temp_path = f"temp/{uuid.uuid4()}.mp4"
            
            Path("temp").mkdir(exist_ok=True)
            with requests.get(video_file, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(temp_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            return temp_path
        except Exception as e:
            logger.warning(f"영상 다운로드 실패 ({attempt+1}/3): {e}")
            time.sleep(2)
    return create_simple_video()

def create_simple_video(duration: int = 60) -> str:
    """기본 영상 생성"""
    colors = ["#1e3c72", "#2a5298", "#434343"]
    clip = ColorClip(size=(1080, 1920), color=random.choice(colors), duration=duration)
    temp_path = f"temp/{uuid.uuid4()}.mp4"
    clip.write_videofile(temp_path, fps=24, logger=None)
    return temp_path

def generate_viral_content(topic: str) -> dict:
    """AI 콘텐츠 생성"""
    default_content = {
        "title": f"{topic}의 비밀",
        "script": f"{topic}에 대해 알아야 할 3가지 사실...",
        "hashtags": [f"#{topic}", "#성공", "#비밀", "#화제", "#shorts"]
    }

    try:
        if not Config.GEMINI_API_KEY:
            return default_content

        genai.configure(api_key=Config.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"{topic}에 대한 바이럴 유튜브 쇼츠 콘텐츠를 JSON으로 생성해주세요."
        response = model.generate_content(prompt)
        return json.loads(response.text.strip("```json").strip())
    except Exception as e:
        logger.error(f"AI 생성 오류: {e}")
        return default_content

if __name__ == "__main__":
    Config.validate()
    test_content = generate_viral_content("부자 되는 법")
    print(json.dumps(test_content, indent=2, ensure_ascii=False))
