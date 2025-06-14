"""
수익 최적화 유틸리티 (2025년 최신 버전)
"""
import os
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

# ✅ 환경 변수 로드
load_dotenv()

# ✅ 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ✅ HEX → RGB 변환 함수
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


def text_to_speech(text: str, output_path: str) -> str:
    """음성 생성 (ElevenLabs API 사용)"""
    try:
        api_key = os.getenv("ELEVENLABS_API_KEY")
        voice_id = os.getenv("ELEVENLABS_VOICE_ID", "uyVNoMrnUku1dZyVEXwD")
        if not api_key:
            raise ValueError("ELEVENLABS_API_KEY가 없습니다.")

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

        logger.info(f"✅ 음성 파일 생성 완료: {output_path}")
        return str(output_path)

    except Exception as e:
        logger.error(f"❌ 음성 생성 실패: {str(e)}")
        raise


def download_video_from_pexels(query: str) -> str:
    """Pexels에서 비디오 다운로드"""
    try:
        api_key = os.getenv("PEXELS_API_KEY")
        if not api_key:
            raise ValueError("PEXELS_API_KEY가 없습니다.")
        headers = {"Authorization": api_key}
        url = f"https://api.pexels.com/videos/search?query={query}&per_page=15&orientation=portrait"

        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        videos = response.json().get("videos", [])

        if not videos:
            raise ValueError("검색 결과 없음")

        video = random.choice(videos)
        video_file = random.choice([f for f in video['video_files'] if f['quality'] == 'sd'])
        video_url = video_file['link']

        Config.ensure_temp_dir()
        video_path = Config.TEMP_DIR / f"{uuid.uuid4()}.mp4"

        with requests.get(video_url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(video_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        logger.info(f"✅ 비디오 다운로드 완료: {video_path}")
        return str(video_path)

    except Exception as e:
        logger.error(f"❌ 비디오 다운로드 실패: {str(e)}. 기본 영상 생성으로 대체합니다.")
        return create_simple_video()


def create_simple_video(duration: int = 60) -> str:
    """기본 배경 영상 생성"""
    try:
        Config.ensure_temp_dir()
        colors = ["#1e3c72", "#2a5298", "#434343", "#000000", (255, 0, 0), (0, 255, 0), (0, 0, 255)]
        chosen_color = random.choice(colors)

        # ✅ HEX 문자열일 경우 RGB로 변환
        if isinstance(chosen_color, str):
            chosen_color = hex_to_rgb(chosen_color)

        video_path = Config.TEMP_DIR / f"{uuid.uuid4()}.mp4"
        clip = ColorClip(size=(Config.SHORTS_WIDTH, Config.SHORTS_HEIGHT), color=chosen_color, duration=duration)
        clip.write_videofile(str(video_path), fps=24, logger=None)
        logger.info(f"✅ 기본 영상 생성 완료: {video_path}")
        return str(video_path)

    except Exception as e:
        logger.error(f"❌ 기본 영상 생성 실패: {str(e)}")
        raise


def generate_viral_content(topic: str) -> dict:
    """바이럴 콘텐츠 생성 (Gemini API 사용)"""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY가 없습니다.")

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash-latest')

        prompt = f"""
        당신은 100만 유튜버를 위한 콘텐츠 전문 작가입니다. 다음 주제로 30초 분량의 YouTube Shorts 대본을 생성해주세요.

        주제: {topic}

        요구사항:
        1. 첫 3초는 강력한 훅 문장으로 시작
        2. 핵심 내용을 2~3가지로 나누어 설명
        3. 시청자 참여 유도 문구 포함
        4. 한국어로 작성

        출력 형식 (JSON):
        {{
            "title": "25자 이내의 제목",
            "script": "300자 내외의 대본",
            "hashtags": ["#키워드1", "#키워드2", "#키워드3"]
        }}
        """

        response = model.generate_content(prompt)
        cleaned = response.text.strip().replace("```json", "").replace("```", "").strip()
        content = json.loads(cleaned)

        logger.info(f"✅ Gemini 콘텐츠 생성 성공: {content['title']}")
        return content

    except Exception as e:
        logger.error(f"❌ Gemini 콘텐츠 생성 실패: {str(e)}. 기본 콘텐츠로 대체합니다.")
        return {
            "title": f"{topic}의 비밀",
            "script": f"여러분은 {topic}에 대해 얼마나 알고 있나요? 오늘은 대부분이 모르는 3가지 비밀을 알려드리겠습니다. 첫째,... 둘째,... 마지막으로 가장 중요한 셋째는... 유용했다면 구독과 좋아요 부탁드립니다!",
            "hashtags": [f"#{topic.replace(' ', '')}", "#꿀팁", "#자기계발"]
        }
위에 나의 코드에 
def create_default_audio(text: str, output_path: str) -> str:
    """gTTS를 이용한 기본 음성 생성"""
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang='ko')
        tts.save(output_path)
        return output_path
    except Exception as e:
        logger.error(f"기본 음성 생성 실패: {str(e)}")
        raise
위의 코드를 추가, 수정, 보완해서 보여줘!!