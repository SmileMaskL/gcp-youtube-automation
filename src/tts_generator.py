import requests
import uuid
from pathlib import Path
from config import Config
import logging

logger = logging.getLogger(__name__)

def generate_tts(script):
    """ElevenLabs로 음성 생성"""
    audio_path = Config.TEMP_DIR / f"audio_{uuid.uuid4()}.mp3"
    
    try:
        headers = {
            "xi-api-key": Config.get_api_key("ELEVENLABS_API_KEY"),
            "Content-Type": "application/json"
        }
        
        data = {
            "text": script,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        response = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{Config.ELEVENLABS_VOICE_ID}",
            headers=headers,
            json=data,
            timeout=30
        )
        response.raise_for_status()
        
        with open(audio_path, "wb") as f:
            f.write(response.content)
            
        logger.info(f"음성 생성 완료: {audio_path}")
        return audio_path
        
    except Exception as e:
        logger.error(f"음성 생성 실패: {e}")
        raise
