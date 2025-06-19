import os
from elevenlabs import Voice, VoiceSettings, generate, play
import logging

logger = logging.getLogger(__name__)

def generate_audio(text: str, output_path: str, api_key: str, voice_id: str = "uyVNoMrnUku1dZyVEXwD"):
    """
    ElevenLabs API를 사용하여 텍스트를 음성으로 변환하고 MP3 파일로 저장합니다.
    Args:
        text (str): 음성으로 변환할 텍스트.
        output_path (str): 음성 파일을 저장할 경로 (예: "output/audio.mp3").
        api_key (str): ElevenLabs API 키.
        voice_id (str): 사용할 목소리 ID (기본값: 안나 킴).
    """
    if not api_key:
        logger.error("ElevenLabs API Key is not provided.")
        raise ValueError("ElevenLabs API Key is missing.")

    if not voice_id:
        logger.error("ElevenLabs Voice ID is not provided.")
        raise ValueError("ElevenLabs Voice ID is missing.")

    try:
        audio = generate(
            text=text,
            voice=Voice(
                voice_id=voice_id,
                settings=VoiceSettings(stability=0.71, similarity_boost=0.5, style=0.0, use_speaker_boost=True)
            ),
            api_key=api_key
        )
        
        # 출력 디렉토리 확인 및 생성
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with open(output_path, "wb") as f:
            for chunk in audio:
                f.write(chunk)
        logger.info(f"Audio successfully generated and saved to {output_path}")

    except Exception as e:
        logger.error(f"Failed to generate audio with ElevenLabs: {e}", exc_info=True)
        raise
