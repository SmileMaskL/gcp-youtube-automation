from elevenlabs import generate, set_api_key
import logging

logger = logging.getLogger(__name__)

class TTSGenerator:
    def __init__(self, api_key):
        try:
            set_api_key(api_key)
            self.api_key = api_key
        except Exception as e:
            logger.error(f"❌ TTS 초기화 실패: {e}")
            raise

    def generate_tts(self, text, voice_id):
        try:
            audio = generate(
                text=text,
                voice=voice_id,
                model="eleven_multilingual_v2"
            )
            logger.info("✅ 음성 생성 성공")
            return audio
        except Exception as e:
            logger.error(f"❌ 음성 생성 실패: {e}")
            return None
