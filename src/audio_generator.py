# src/audio_generator.py

import logging
from elevenlabs.client import ElevenLabs

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def generate_audio_from_text(text, api_key, voice_id, output_path):
    """
    ElevenLabs TTS → MP3 저장
    """
    try:
        # ✅ ElevenLabs Client 객체 생성
        client = ElevenLabs(api_key=api_key)
        
        # ✅ TTS 음성 생성
        audio = client.generate(text=text, voice=voice_id)
        
        # ✅ 생성된 오디오 바이너리를 파일로 저장
        with open(output_path, "wb") as f:
            f.write(audio)
        
        logger.info(f"✅ Audio saved to '{output_path}'")
    
    except Exception as e:
        logger.error(f"❌ TTS 생성 실패: {e}")
        raise
