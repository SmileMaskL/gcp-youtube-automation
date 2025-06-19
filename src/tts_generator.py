import os
from elevenlabs import Voice, VoiceSettings, generate, play
from elevenlabs.client import ElevenLabs
from pathlib import Path
from src.config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, AUDIO_DIR, MAX_ELEVENLABS_CHARS_PER_DAY
from src.monitoring import log_system_health
from src.usage_tracker import api_usage_tracker

def generate_audio(text, output_filename="audio.mp3"):
    """
    텍스트를 ElevenLabs를 사용하여 음성으로 변환하고 MP3 파일로 저장합니다.
    """
    if not api_usage_tracker.check_limit("elevenlabs_chars", api_usage_tracker.get_usage("elevenlabs_chars") + len(text), MAX_ELEVENLABS_CHARS_PER_DAY):
        log_system_health("ElevenLabs API 일일 사용 한도(문자 수) 초과. 오디오를 생성할 수 없습니다.", level="warning")
        raise ValueError("ElevenLabs API 한도 초과. 오디오를 생성할 수 없습니다.")

    if not ELEVENLABS_API_KEY:
        log_system_health("ElevenLabs API Key가 설정되지 않았습니다.", level="error")
        raise ValueError("ElevenLabs API Key가 설정되지 않았습니다. 오디오를 생성할 수 없습니다.")

    client = ElevenLabs(
        api_key=ELEVENLABS_API_KEY,
    )

    output_path = os.path.join(AUDIO_DIR, output_filename)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    try:
        # Voice 객체를 사용하여 특정 Voice ID 지정
        audio = client.generate(
            text=text,
            voice=Voice(
                voice_id=ELEVENLABS_VOICE_ID,
                settings=VoiceSettings(stability=0.75, similarity_boost=0.75, style=0.0, use_speaker_boost=True)
            ),
            model="eleven_multilingual_v2" # 한국어 지원 모델
        )

        # audio 객체는 StreamingResponse를 포함할 수 있으므로, content를 직접 저장
        with open(output_path, "wb") as f:
            for chunk in audio.iter_bytes(chunk_size=4096):
                f.write(chunk)

        api_usage_tracker.record_usage("elevenlabs_chars", count=len(text))
        log_system_health(f"오디오 파일이 성공적으로 생성되었습니다: {output_path} (문자 수: {len(text)})", level="info")
        return output_path
    except Exception as e:
        log_system_health(f"ElevenLabs 오디오 생성 중 오류 발생: {e}", level="error")
        raise ValueError(f"ElevenLabs 오디오 생성 실패: {e}")

# For local testing (optional)
if __name__ == "__main__":
    try:
        test_text = "안녕하세요. 이것은 ElevenLabs를 이용한 한국어 음성 테스트입니다."
        output_file = "test_audio.mp3"
        audio_path = generate_audio(test_text, output_file)
        print(f"Test audio saved to: {audio_path}")
        # play(audio_path) # 로컬에서 재생하려면 elevenlabs.play() 주석 해제
    except ValueError as e:
        print(f"Error during test: {e}")
