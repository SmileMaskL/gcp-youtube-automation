import logging
import os
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, ImageClip, ColorClip
from elevenlabs import ElevenLabs

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

def generate_audio_from_text(text: str) -> str:
    """텍스트를 오디오로 변환하고 저장"""
    try:
        audio = client.generate(
            text=text,
            voice=ELEVENLABS_VOICE_ID,
            model="eleven_multilingual_v2"
        )
        output_audio_path = "output/output.mp3"
        os.makedirs("output", exist_ok=True)
        client.save(audio, output_audio_path)
        logging.info(f"✅ 오디오 생성 완료: {output_audio_path}")
        return output_audio_path
    except Exception as e:
        logging.error(f"🛑 ElevenLabs 오디오 생성 실패: {e}")
        raise

def create_video():
    """영상 생성 예시"""
    logging.info("🎬 영상 생성 시작")
    text_to_speak = "안녕하세요. 이것은 자동화된 유튜브 비디오의 예시입니다."

    try:
        audio_file = generate_audio_from_text(text_to_speak)
    except Exception as e:
        logging.error("오디오 생성 실패로 영상 생성 중단")
        return

    audio_clip = AudioFileClip(audio_file)
    duration = audio_clip.duration + 2

    video_clip = ColorClip(size=(1080, 1920), color=(0, 0, 0), duration=duration).set_audio(audio_clip)
    output_video_path = "output/final_video.mp4"
    video_clip.write_videofile(output_video_path, fps=24, codec="libx264", audio_codec="aac")

    logging.info(f"✅ 영상 생성 완료: {output_video_path}")
