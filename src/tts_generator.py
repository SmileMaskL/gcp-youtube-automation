import os
import requests
from typing import Optional  # ✅ 추가
from src.config import Config

class TTSGenerator:
    def __init__(self, api_key):
        self.api_key = api_key

    def generate_tts(text: str, voice_id: str, output_dir: str = "temp") -> Optional[str]:
        """ElevenLabs API를 사용해 TTS 생성"""
        try:
            api_key = Config.get_elevenlabs_key()
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        
            headers = {
                "xi-api-key": api_key,
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
        
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, "tts_audio.mp3")
            with open(output_path, "wb") as f:
                f.write(response.content)
        
            return output_path
        except Exception as e:
            print(f"TTS 생성 오류: {e}")
            return None
