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
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

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
    """gTTS로 기본 음성 생성"""
    try:
        from gtts import gTTS
        logger.info("✅ gTTS로 음성 생성 중...")
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        tts = gTTS(text=text, lang='ko')
        tts.save(str(output_path))
        logger.info(f"🔊 gTTS 음성 저장 완료: {output_path}")
        return str(output_path)
    except Exception as e:
        logger.error(f"❌ gTTS 실패: {e}")
        raise RuntimeError("모든 음성 생성 실패")

def text_to_speech(text: str, output_path: str, fallback: bool = True) -> str:
    """음성 생성 (ElevenLabs 실패 시 gTTS fallback)"""
    try:
        api_key = os.getenv("ELEVENLABS_API_KEY")
        voice_id = os.getenv("ELEVENLABS_VOICE_ID", "uyVNoMrnUku1dZyVEXwD")
        if not api_key:
            raise ValueError("ELEVENLABS_API_KEY 없음")

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

        logger.info(f"🎙️ ElevenLabs 음성 저장 완료: {output_path}")
        return str(output_path)

    except Exception as e:
        logger.warning(f"⚠️ ElevenLabs 실패: {e}")
        if fallback:
            return create_default_audio(text, output_path)
        raise

def create_simple_video():
    """pexels 실패 시 fallback 비디오"""
    fallback_path = Path("temp/default_video.mp4")
    fallback_path.parent.mkdir(exist_ok=True)
    clip = ColorClip(size=(1080, 1920), color=(
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255)
    ), duration=60)
    clip.write_videofile(str(fallback_path), fps=24)
    return str(fallback_path)

def download_video_from_pexels(query: str) -> str:
    try:
        api_key = os.getenv("PEXELS_API_KEY")
        if not api_key:
            raise ValueError("PEXELS_API_KEY 없음")

        headers = {"Authorization": api_key}
        url = f"https://api.pexels.com/videos/search?query={query}&per_page=20&orientation=portrait&size=small"
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        if not data.get('videos'):
            raise ValueError("관련 비디오 없음")

        video = max(data['videos'], key=lambda x: x.get('duration', 0))
        video_file = next((f for f in video['video_files'] if f['quality'] == 'sd' and f['width'] == 640), None)

        if not video_file:
            raise ValueError("적절한 비디오 파일 없음")

        Config.ensure_temp_dir()
        video_path = Config.TEMP_DIR / f"{uuid.uuid4()}.mp4"
        with requests.get(video_file['link'], stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(video_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        logger.info(f"📹 Pexels 영상 다운로드 완료: {video_path}")
        return str(video_path)

    except Exception as e:
        logger.error(f"⚠️ Pexels 영상 실패, 기본 영상 사용: {e}")
        return create_simple_video()

def generate_viral_content(topic: str) -> dict:
    """Gemini 기반 바이럴 콘텐츠 생성"""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY 없음")

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash-latest')

        prompt = f"""당신은 수익형 유튜브 쇼츠 전문가입니다.
'제목:'과 '본문:' 형식으로 '{topic}'에 대한 바이럴 쇼츠 콘텐츠를 생성해주세요. 반드시 한글로 작성해주세요."""
        response = model.generate_content(prompt)

        result = response.text
        match = re.search(r"제목:\s*(.+?)\n본문:\s*(.+)", result, re.DOTALL)
        if match:
            title = match.group(1).strip()
            script = match.group(2).strip()
        else:
            raise ValueError("정규식 추출 실패")

        hashtags = [f"#{topic}", "#쇼츠", "#수익"]

        return {"title": title, "script": script, "hashtags": hashtags}

    except Exception as e:
        logger.warning(f"⚠️ Gemini 실패: {e}. 기본 템플릿 사용")
        return {
            "title": f"{topic}의 놀라운 비법",
            "script": f"{topic}으로 돈 버는 법이 궁금하다면 이 영상은 꼭 봐야 합니다!",
            "hashtags": [f"#{topic}", "#수익", "#부업"]
        }

# 테스트 예제 (직접 실행용)
if __name__ == "__main__":
    Config.ensure_temp_dir()
    topic = "자동 수익 창출"
    content = generate_viral_content(topic)
    print(f"🎯 제목: {content['title']}")
    audio = text_to_speech(content['script'], "temp/audio.mp3")
    video = download_video_from_pexels("money")
    print(f"✅ 음성: {audio}\n✅ 영상: {video}")
