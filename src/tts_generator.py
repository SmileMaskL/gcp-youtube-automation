import logging
from elevenlabs import Voice, VoiceSettings, generate, save

logger = logging.getLogger(__name__)

def generate_tts_audio(elevenlabs_api_key, text_content, voice_id, output_path):
    try:
        logger.info(f"ElevenLabs 음성 생성 시작. 음성 ID: {voice_id}, 텍스트 길이: {len(text_content)}")
        
        audio = generate(
            text=text_content,
            voice=Voice(
                voice_id=voice_id,
                settings=VoiceSettings(
                    stability=0.7,
                    similarity_boost=0.8,
                    style=0.0,
                    use_speaker_boost=True
                )
            ),
            api_key=elevenlabs_api_key
        )
        
        save(audio, output_path)
        logger.info(f"음성 파일 생성 성공: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"ElevenLabs 음성 생성 실패: {e}", exc_info=True)
        raise
