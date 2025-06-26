# src/tts_generator.py

import os
import logging
from elevenlabs import play, generate, Voice, save # ElevenLabs 라이브러리의 올바른 함수와 클래스 임포트
from elevenlabs.types import Voice, VoiceSettings # Voice, VoiceSettings는 그대로 유지

logger = logging.getLogger(__name__)

def generate_tts_audio(api_key: str, content: str, voice_id: str, file_path: str) -> None:
    """
    텍스트를 Eleven Labs를 사용하여 음성 오디오로 변환하고 저장합니다.
    """
    if not api_key or not voice_id:
        logger.error("❌ ElevenLabs API Key 또는 Voice ID가 설정되지 않았습니다.")
        raise ValueError("ElevenLabs API Key 또는 Voice ID가 설정되지 않았습니다.")

    # ElevenLabs 클라이언트 초기화 (API 키 직접 전달)
    client = ElevenLabs(api_key=api_key) # API 키를 직접 전달하도록 수정

    try:
        logger.info(f"ElevenLabs TTS 생성 시작. Voice ID: {voice_id}")
        audio = client.generate(
            text=content,
            voice=Voice(
                voice_id=voice_id,
                settings=VoiceSettings(stability=0.75, similarity_boost=0.75)
            ),
            model="eleven_multilingual_v2" # 필요에 따라 모델 지정 가능
        )
        
        # audio 객체는 이터러블이므로, 파일에 직접 쓰는 방식으로 저장
        with open(file_path, "wb") as f:
            for chunk in audio:
                f.write(chunk)

        logger.info(f"✅ 음성 오디오가 성공적으로 '{file_path}'에 저장되었습니다.")
    except Exception as e:
        logger.error(f"🔥 음성 오디오 생성 중 오류 발생: {e}", exc_info=True)
        raise RuntimeError(f"음성 오디오 생성 중 오류 발생: {e}")
