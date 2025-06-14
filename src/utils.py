"""
수익 최적화 유틸리티 (2025년 최신 버전)
"""
import os
import re
import requests
import json
import logging
import time
import uuid
import random
from pathlib import Path
from moviepy.editor import ColorClip
from elevenlabs import Voice, VoiceSettings
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv
import google.generativeai as genai

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def hex_to_rgb(hex_color):
    """HEX 문자열 (#RRGGBB) → RGB 튜플 (R, G, B)"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

class Config:
    """설정 클래스"""
    SHORTS_WIDTH = 1080
    SHORTS_HEIGHT = 1920
    MAX_DURATION = 60
    MIN_DURATION = 15
    TEMP_DIR = Path("temp")

    @classmethod
    def ensure_temp_dir(cls):
        cls.TEMP_DIR.mkdir(exist_ok=True)

def create_default_audio(text: str, output_path: str) -> str:
    """gTTS를 이용한 기본 음성 생성"""
    try:
        from gtts import gTTS
        logger.info("Using gTTS as fallback TTS service...")
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        tts = gTTS(text=text, lang='ko', slow=False)
        tts.save(str(output_path))
        
        logger.info(f"Audio generated with gTTS: {output_path}")
        return str(output_path)
    except Exception as e:
        logger.error(f"gTTS failed: {str(e)}")
        raise RuntimeError("All TTS methods failed")

def text_to_speech(text: str, output_path: str, fallback: bool = True) -> str:
    """음성 생성 (ElevenLabs 우선 시도, 실패 시 gTTS)"""
    try:
        # ElevenLabs 시도
        api_key = os.getenv("ELEVENLABS_API_KEY")
        voice_id = os.getenv("ELEVENLABS_VOICE_ID", "uyVNoMrnUku1dZyVEXwD")
        
        if not api_key:
            logger.warning("ELEVENLABS_API_KEY not found")
            raise ValueError("API key missing")

        client = ElevenLabs(api_key=api_key)
        audio = client.generate(
            text=text,
            voice=Voice(
                voice_id=voice_id,
                settings=VoiceSettings(stability=0.5, similarity_boost=0.75)
            ),
            model="eleven_multilingual_v2"
        )

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "wb") as f:
            for chunk in audio:
                f.write(chunk)

        logger.info(f"ElevenLabs audio generated: {output_path}")
        return str(output_path)

    except Exception as e:
        logger.warning(f"ElevenLabs failed: {str(e)}")
        if fallback:
            return create_default_audio(text, output_path)
        raise

def download_video_from_pexels(query: str) -> str:
    try:
        api_key = os.getenv("PEXELS_API_KEY")
        if not api_key:
            raise ValueError("PEXELS_API_KEY missing")
            
        headers = {"Authorization": api_key}
        url = f"https://api.pexels.com/videos/search?query={query}&per_page=20&orientation=portrait&size=small"

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if not data.get('videos'):
            raise ValueError("No videos found for the query")

        # 가장 인기있는 동영상 선택 (조회수 기준)
        video = max(data['videos'], key=lambda x: x.get('duration', 0))
        
        # 고화질 비디오 파일 선택
        video_file = next(
            (f for f in video['video_files'] 
            if f['quality'] == 'sd' and f['width'] == 640
        )
        
        Config.ensure_temp_dir()
        video_path = Config.TEMP_DIR / f"{uuid.uuid4()}.mp4"

        with requests.get(video_file['link'], stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(video_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        logger.info(f"Video downloaded: {video_path}")
        return str(video_path)

    except Exception as e:
        logger.error(f"Video download failed, using fallback: {str(e)}")
        return create_simple_video()

def generate_viral_content(topic: str) -> dict:
    """바이럴 콘텐츠 생성"""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY missing")

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash-latest')

        prompt = f"""Generate viral YouTube Shorts content in Korean about {topic}."""
        
        response = model.generate_content(prompt)

        # JSON 응답 강제 추출
        response_text = response.text
        json_str = re.search(r'\{.*\}', response_text, re.DOTALL).group()
        content = json.loads(json_str)

        # 필수 필드 검증
        if not all(key in content for key in ['title', 'script', 'hashtags']):
            raise ValueError("필수 필드 누락")
            
        return content

    except Exception as e:
        logger.warning(f"콘텐츠 생성 실패: {str(e)}. 기본 템플릿 사용")
        return {
            "title": f"{topic}의 놀라운 비법",
            "script": f"이 동영상을 보시면 {topic}으로 돈 버는 방법이 완전히 바뀝니다! 지금 바로 따라해보세요!",
            "hashtags": [f"#{topic}", "#수익", "#부업"]
        }

        # content = json.loads(response.text.strip())
        
        logger.info(f"Content generated: {content.get('title')}")
        return content

    except Exception as e:
        logger.error(f"Content generation failed: {str(e)}")
        return {
            "title": f"{topic}의 비밀",
            "script": f"여러분은 {topic}에 대해 얼마나 알고 있나요? 오늘은 대부분이 모르는 3가지 비밀을 알려드리겠습니다.",
            "hashtags": [f"#{topic}", "#shorts", "#viral"]
        }

# 사용 예제
if __name__ == "__main__":
    try:
        Config.ensure_temp_dir()
        
        # 콘텐츠 생성
        content = generate_viral_content("자동 수익 창출")
        print(f"제목: {content['title']}")
        
        # 음성 생성 (ElevenLabs 실패 시 gTTS 자동 대체)
        audio_path = text_to_speech(
            text=content["script"],
            output_path=str(Config.TEMP_DIR / "audio.mp3")
        )
        
        # 비디오 다운로드 (실패 시 기본 영상 생성)
        video_path = download_video_from_pexels("money")
        
        print(f"모든 리소스 생성 완료!\n음성: {audio_path}\n영상: {video_path}")
        
    except Exception as e:
        logger.error(f"메인 프로세스 실패: {str(e)}")
