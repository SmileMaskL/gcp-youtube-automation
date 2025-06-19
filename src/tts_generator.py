"""
TTS 생성 모듈 (최종 수정본)
"""
import os
import requests
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def generate_tts(text, voice_id="uyVNoMrnUku1dZyVEXwD"):
    try:
        url = "https://api.elevenlabs.io/v1/text-to-speech/" + voice_id
        headers = {
            "xi-api-key": os.getenv("ELEVENLABS_API_KEY"),
            "Content-Type": "application/json"
        }
        data = {
            "text": text,
            "voice_settings": {
                "stability": 0.7,
                "similarity_boost": 0.8
            }
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        
        os.makedirs("temp", exist_ok=True)
        audio_path = f"temp/audio_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp3"
        
        with open(audio_path, "wb") as f:
            f.write(response.content)
            
        return audio_path
    except Exception as e:
        logger.error(f"TTS 생성 실패: {str(e)}")
        raise
