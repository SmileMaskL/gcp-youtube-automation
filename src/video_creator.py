import logging
import os
from moviepy.editor import AudioFileClip, ColorClip
from elevenlabs.client import ElevenLabs
from elevenlabs.types import Voice, VoiceSettings

# ✅ 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ✅ 환경변수에서 API 키와 보이스 ID 불러오기
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

if not ELEVENLABS_API_KEY or not ELEVENLABS_VOICE_ID:
    logging.error("❌ ELEVENLABS_API_KEY 또는 ELEVENLABS_VOICE_ID가 없습니다.")
    raise ValueError("❗ ElevenLabs API Key 및 Voice ID는 필수입니다.")

# ✅ ElevenLabs 클라이언트 초기화
client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

# ✅ 텍스트를 음성으로 변환하고 mp3 저장
def generate_audio(text: str, output_path: str = "output/output.mp3", voice_settings: VoiceSettings = None) -> str:
    try:
        if voice_settings is None:
            voice_settings = VoiceSettings(
                stability=0.5,
                similarity_boost=0.75,
                style=0.0,
                speaker_boost=True
            )
        voice = Voice(
            voice_id=ELEVENLABS_VOICE_ID,
            settings=voice_settings
        )

        logging.info("🎙️ 텍스트를 음성으로 변환 중...")
        audio = client.generate(
            text=text,
            voice=voice,
            model="eleven_multilingual_v2"
        )

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(audio)

        logging.info(f"✅ 오디오 생성 완료: {output_path}")
        return output_path

    except Exception as e:
        logging.error(f"❌ ElevenLabs 음성 생성 실패: {e}")
        raise

# ✅ 오디오를 기반으로 영상 생성 (Shorts용: 1080x1920)
def create_video(text: str, output_path: str = "output/final_video.mp4") -> str:
    try:
        logging.info("🎬 영상 생성 시작")
        audio_file = generate_audio(text)
        audio_clip = AudioFileClip(audio_file)
        duration = audio_clip.duration + 2  # 끝 여유시간 2초

        # 영상 클립 (검정 배경)
        video_clip = ColorClip(size=(1080, 1920), color=(0, 0, 0), duration=duration)
        video_clip = video_clip.set_audio(audio_clip)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        video_clip.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")

        audio_clip.close()
        video_clip.close()
        logging.info(f"✅ 영상 생성 완료: {output_path}")
        return output_path

    except Exception as e:
        logging.error(f"❌ 영상 생성 실패: {e}")
        raise
