"""
수익 최적화 유튜브 자동화 유틸리티 (완전한 버전)
- 역할: AI 대본 생성, TTS, 영상 다운로드 등 핵심 도구 모음 (순수 공구함)
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

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def text_to_speech(text: str, output_path: str) -> str:
    logger.info("음성 생성을 시작합니다...")
    try:
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            raise ValueError("환경 변수에서 ELEVENLABS_API_KEY를 찾을 수 없습니다.")

        client = ElevenLabs(api_key=api_key)
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
        
        logger.info(f"음성 파일이 성공적으로 '{output_path}'에 저장되었습니다.")
        return output_path
    except Exception as e:
        logger.error(f"ElevenLabs 음성 생성 중 오류 발생: {e}")
        raise

def download_video_from_pexels(query: str) -> str:
    logger.info(f"'{query}' 관련 영상 다운로드를 시작합니다...")
    try:
        api_key = os.getenv("PEXELS_API_KEY")
        if not api_key:
            logger.warning("PEXELS_API_KEY가 없습니다. 기본 단색 배경 영상을 생성합니다.")
            return create_simple_video()

        money_keywords = ["luxury", "success", "motivation", "business", "travel", "finance", "investment", "technology"]
        search_query = query or random.choice(money_keywords)
        headers = {"Authorization": api_key}
        url = f"https://api.pexels.com/videos/search?query={search_query}&per_page=15&orientation=portrait"

        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        videos = response.json().get("videos", [])
        if not videos:
            logger.warning(f"'{search_query}'에 대한 영상 결과가 없습니다. 기본 영상을 생성합니다.")
            return create_simple_video()

        video = random.choice(videos)
        video_link = random.choice(video['video_files'])['link']
        
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        temp_path = temp_dir / f"{uuid.uuid4()}.mp4"

        with requests.get(video_link, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(temp_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        
        logger.info(f"영상이 성공적으로 '{temp_path}'에 다운로드되었습니다.")
        return str(temp_path)
    except Exception as e:
        logger.error(f"Pexels 영상 다운로드 실패: {e}. 기본 영상을 생성합니다.")
        return create_simple_video()

def create_simple_video(duration: int = 60) -> str:
    logger.info("기본 배경 영상을 생성합니다.")
    try:
        colors = ["#1e3c72", "#2a5298", "#434343", "#000000"]
        clip = ColorClip(size=(1080, 1920), color=random.choice(colors), duration=duration)
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        temp_path = temp_dir / f"{uuid.uuid4()}.mp4"
        clip.write_videofile(str(temp_path), fps=24, logger=None)
        return str(temp_path)
    except Exception as e:
        logger.critical(f"기본 영상 생성 중 치명적 오류 발생: {e}")
        raise

def generate_viral_content(topic: str) -> dict:
    logger.info(f"'{topic}' 주제로 바이럴 콘텐츠 생성을 시작합니다...")
    try:
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        prompt = f"""
        당신은 100만 유튜버를 만든 바이럴 쇼츠 콘텐츠 전문 작가입니다.
        주제: {topic}
        **필수 조건:**
        1.  **훅 (Hook, 첫 3초):** 시청자의 스크롤을 즉시 멈출 강력한 한 문장으로 시작.
        2.  **본문 (Body):** 핵심 내용을 2~3가지로 나누어 빠르고 흥미롭게 설명.
        3.  **결론 (Conclusion):** 행동을 유도하는 문구(Call to Action)를 포함하여 마무리.
        **출력 형식 (오직 JSON 형식만 출력):**
        {{
            "title": "클릭을 유발하는 25자 내외의 제목",
            "script": "훅, 본문, 결론을 포함한 350자 내외의 완벽한 대본",
            "hashtags": ["#핵심키워드", "#관련토픽", "#바이럴", "#꿀팁", "#shorts"]
        }}
        """
        response = model.generate_content(prompt)
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "").strip()
        content = json.loads(cleaned_response)
        logger.info("Gemini 콘텐츠 생성이 성공적으로 완료되었습니다.")
        return content
    except Exception as e:
        logger.error(f"Gemini 콘텐츠 생성 실패: {e}. 비상용 기본 콘텐츠를 사용합니다.")
        return {
            "title": f"몰랐으면 손해! {topic}의 모든 것",
            "script": f"혹시 {topic}에 대해 얼마나 아시나요? 대부분이 모르는 3가지 비밀을 지금부터 알려드릴게요. 첫째,... 둘째,... 마지막으로 가장 중요한 셋째는... 이 정보가 유용했다면 구독과 좋아요 잊지 마세요!",
            "hashtags": [f"#{''.join(filter(str.isalnum, topic))}", "#꿀팁", "#자기계발", "#성공", "#shorts"]
        }
