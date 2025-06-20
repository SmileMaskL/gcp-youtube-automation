import logging
import os
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, ImageClip, ColorClip
from elevenlabs.client import ElevenLabs
from elevenlabs import Voice, VoiceSettings

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 환경변수에서 ElevenLabs API Key와 Voice ID 불러오기
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

if not ELEVENLABS_API_KEY or not ELEVENLABS_VOICE_ID:
    logging.error("❌ ELEVENLABS_API_KEY 또는 ELEVENLABS_VOICE_ID가 설정되지 않았습니다.")
    raise ValueError("ElevenLabs API Key 및 Voice ID가 필요합니다.")

# ElevenLabs 클라이언트 초기화
client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

def generate_audio_from_text(text: str, voice_settings: VoiceSettings = None) -> str:
    """텍스트를 오디오로 변환하고 저장"""
    try:
        if voice_settings is None:
            voice_settings = VoiceSettings(
                stability=0.5,
                similarity_boost=0.7,
                style=0.0,
                speaker_boost=True
            )

        audio = client.generate(
            text=text,
            voice=Voice(
                voice_id=ELEVENLABS_VOICE_ID,
                settings=voice_settings
            ),
            model="eleven_multilingual_v2"
        )

        output_audio_path = "output/output.mp3"
        os.makedirs("output", exist_ok=True)

        with open(output_audio_path, "wb") as f:
            f.write(audio)

        logging.info(f"✅ 오디오 생성 완료: {output_audio_path}")
        return output_audio_path
    except Exception as e:
        logging.error(f"🛑 ElevenLabs 오디오 생성 실패: {e}")
        raise

def create_video():
    """영상 생성 메인 함수"""
    logging.info("🎬 영상 생성 시작")
    text_to_speak = "안녕하세요. 이것은 자동화된 유튜브 비디오의 예시입니다."

    try:
        custom_voice_settings = VoiceSettings(
            stability=0.7,
            similarity_boost=0.8,
            style=0.2,
            speaker_boost=True
        )

        audio_file = generate_audio_from_text(text_to_speak, custom_voice_settings)
        audio_clip = AudioFileClip(audio_file)

        duration = audio_clip.duration + 2

        video_clip = ColorClip(
            size=(1080, 1920),
            color=(0, 0, 0),
            duration=duration
        ).set_audio(audio_clip)

        output_video_path = "output/final_video.mp4"

        video_clip.write_videofile(
            output_video_path,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            threads=4,
            preset='fast',
            bitrate="5000k"
        )

        logging.info(f"✅ 영상 생성 완료: {output_video_path}")
        return output_video_path

    except Exception as e:
        logging.error(f"🛑 영상 생성 실패: {e}")
        raise
    finally:
        if 'audio_clip' in locals():
            audio_clip.close()
        if 'video_clip' in locals():
            video_clip.close()

def example_voice_generation():
    """예제: 음성 생성 및 저장 테스트"""
    try:
        test_audio = client.generate(
            text="안녕하세요. 오늘의 영상입니다.",
            voice=Voice(
                voice_id=ELEVENLABS_VOICE_ID,
                settings=VoiceSettings(
                    stability=0.6,
                    similarity_boost=0.75,
                    style=0.1,
                    speaker_boost=True
                )
            ),
            model="eleven_multilingual_v2"
        )

        test_output_path = "output/test_audio.mp3"
        os.makedirs("output", exist_ok=True)

        with open(test_output_path, "wb") as f:
            f.write(test_audio)

        logging.info(f"✅ 테스트 오디오 저장 완료: {test_output_path}")

    except Exception as e:
        logging.error(f"🛑 테스트 오디오 생성 실패: {e}")

if __name__ == "__main__":
    os.makedirs("output", exist_ok=True)
    example_voice_generation()
    create_video()
