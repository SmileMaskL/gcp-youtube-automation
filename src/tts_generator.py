# tts_generator.py (수정 후)

import os
from elevenlabs import ElevenLabs  # ElevenLabs 클라이언트 임포트
from elevenlabs.types import Voice, VoiceSettings # Voice, VoiceSettings는 그대로 유지

def generate_tts_audio(text: str, file_path: str) -> None:
    """
    텍스트를 Eleven Labs를 사용하여 음성 오디오로 변환하고 저장합니다.
    """
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    voice_id = os.environ.get("ELEVENLABS_VOICE_ID")

    if not api_key or not voice_id:
        print("ElevenLabs API Key 또는 Voice ID가 설정되지 않았습니다.")
        return

    # ElevenLabs 클라이언트 초기화
    client = ElevenLabs(api_key=api_key)

    try:
        audio = client.generate(
            text=text,
            voice=Voice(
                voice_id=voice_id,
                settings=VoiceSettings(stability=0.75, similarity_boost=0.75)
            )
        )
        
        # client.save 함수는 직접 파일 경로를 인자로 받지 않습니다.
        # 대신, audio 객체에서 직접 파일로 저장하거나, stremaing_player 등을 사용해야 합니다.
        # 여기서는 가장 간단한 파일 저장 방식을 사용합니다.
        with open(file_path, "wb") as f:
            for chunk in audio:
                f.write(chunk)

        print(f"음성 오디오가 성공적으로 '{file_path}'에 저장되었습니다.")
    except Exception as e:
        print(f"음성 오디오 생성 중 오류 발생: {e}")
