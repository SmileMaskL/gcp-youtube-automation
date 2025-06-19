import os
import logging
from elevenlabs import generate, set_api_key, Voice, VoiceSettings
from src.config import Config

logger = logging.getLogger(__name__)

def generate_tts(text: str, voice_id: str, output_dir: str = "temp") -> Optional[str]:
    """
    ElevenLabs API를 사용하여 텍스트를 음성으로 변환합니다.
    Args:
        text: 음성으로 변환할 텍스트.
        voice_id: ElevenLabs에서 사용할 음성 ID.
        output_dir: 음성 파일을 저장할 디렉토리.
    Returns:
        생성된 오디오 파일의 경로 또는 None (실패 시).
    """
    try:
        elevenlabs_api_key = Config.get_elevenlabs_api_key()
        if not elevenlabs_api_key:
            raise ValueError("ELEVENLABS_API_KEY가 설정되지 않았습니다.")
        
        set_api_key(elevenlabs_api_key)

        os.makedirs(output_dir, exist_ok=True)
        timestamp = int(os.times().system * 1000) # 시스템 시간 기반으로 고유한 이름 생성
        audio_filename = f"audio_{timestamp}.mp3"
        audio_path = os.path.join(output_dir, audio_filename)

        # VoiceSettings는 음성의 안정성, 명확성 등을 조절할 수 있습니다.
        # 필요에 따라 이 값을 조절하여 더 나은 품질의 음성을 얻을 수 있습니다.
        audio = generate(
            text=text,
            voice=Voice(
                voice_id=voice_id,
                settings=VoiceSettings(stability=0.75, similarity_boost=0.75, style=0.0, use_speaker_boost=True)
            ),
            model="eleven_multilingual_v2" # 한국어 지원 모델
        )

        with open(audio_path, 'wb') as f:
            f.write(audio)
        
        logger.info(f"TTS 생성 성공: {audio_path}")
        return audio_path
    except Exception as e:
        logger.error(f"TTS 생성 실패: {e}", exc_info=True)
        return None
