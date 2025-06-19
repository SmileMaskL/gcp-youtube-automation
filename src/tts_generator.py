import os
import logging
from elevenlabs import generate, Voice, VoiceSettings, set_api_key

logger = logging.getLogger(__name__)

def generate_audio(text: str, output_path: str, api_key: str, voice_id: str = "uyVNoMrnUku1dZyVEXwD"):
    if not api_key:
        logger.error("ElevenLabs API Key is not provided.")
        raise ValueError("ElevenLabs API Key is missing.")
    
    set_api_key(api_key)  # API 키 설정
    
    try:
        audio = generate(
            text=text,
            voice=Voice(
                voice_id=voice_id,
                settings=VoiceSettings(stability=0.71, similarity_boost=0.5, style=0.0, use_speaker_boost=True)
            )
        )
        
        # 출력 디렉토리 생성
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, "wb") as f:
            f.write(audio)  # 오디오 바이트 저장
        
        logger.info(f"Audio saved to {output_path}")
        return True

    except Exception as e:
        logger.error(f"ElevenLabs API error: {e}")
        return False
