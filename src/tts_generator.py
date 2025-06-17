import os
import uuid
import requests
from pathlib import Path
from config import Config
from retrying import retry
import logging

logger = logging.getLogger(__name__)

@retry(stop_max_attempt_number=3, wait_fixed=2000)
def generate_tts(script):
    """음성 생성 (ElevenLabs)"""
    audio_path = Config.TEMP_DIR / f"audio_{uuid.uuid4()}.mp3"
    try:
        headers = {
            "xi-api-key": Config.get_api_key("ELEVENLABS_API_KEY"),
            "Content-Type": "application/json"
        }
        data = {
            "text": script,
            "model_id": "eleven_multilingual_v2",  # 다국어 모델
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        response = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/uyVNoMrnUku1dZyVEXwD",  # 안나 킴 목소리
            headers=headers,
            json=data,
            timeout=30
        )
        response.raise_for_status()
        with open(audio_path, "wb") as f:
            f.write(response.content)
        return audio_path
    except Exception as e:
        logger.error(f"음성 생성 실패: {e}")
        raise
