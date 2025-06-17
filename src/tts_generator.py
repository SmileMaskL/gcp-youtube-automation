import requests
import uuid
from pathlib import Path
from config import Config

def generate_tts(script):
    audio_path = Config.TEMP_DIR / f"audio_{uuid.uuid4()}.mp3"
    headers = {"xi-api-key": Config.get_api_key("ELEVENLABS_API_KEY")}
    
    response = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{Config.ELEVENLABS_VOICE_ID}",
        headers=headers,
        json={"text": script, "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}},
        timeout=30
    )
    response.raise_for_status()
    
    with open(audio_path, "wb") as f:
        f.write(response.content)
    return audio_path
