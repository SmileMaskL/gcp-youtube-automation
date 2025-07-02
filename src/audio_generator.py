# src/audio_generator.py

import logging
from elevenlabs import generate, save

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def generate_audio_from_text(text, api_key, voice_id, output_path):
    """
    ElevenLabs TTS → MP3 저장
    """
    try:
        from elevenlabs import set_api_key
        set_api_key(api_key)
        audio = generate(text=text, voice=voice_id)
        save(audio, output_path)
        logger.info(f"✅ Audio saved to '{output_path}'")
    except Exception as e:
        logger.error(f"❌ TTS 생성 실패: {e}")
        raise
