import logging
import os
from moviepy.editor import AudioFileClip, ColorClip
from elevenlabs.client import ElevenLabs
from elevenlabs import Voice, VoiceSettings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

if not ELEVENLABS_API_KEY or not ELEVENLABS_VOICE_ID:
    logging.error("ELEVENLABS_API_KEY 또는 ELEVENLABS_VOICE_ID가 없습니다.")
    raise ValueError("ElevenLabs API Key 및 Voice ID가 필요합니다.")

client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

def generate_audio_from_text(text: str, voice_settings: VoiceSettings = None) -> str:
    try:
        if voice_settings is None:
            voice_settings = VoiceSettings(stability=0.5, similarity_boost=0.7, style=0.0, speaker_boost=True)
        audio = client.generate(
            text=text,
            voice=Voice(voice_id=ELEVENLABS_VOICE_ID, settings=voice_settings),
            model="eleven_multilingual_v2"
        )
        output_path = "output/output.mp3"
        os.makedirs("output", exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(audio)
        logging.info(f"오디오 생성 완료: {output_path}")
        return output_path
    except Exception as e:
        logging.error(f"ElevenLabs 음성 생성 실패: {e}")
        raise

def create_video(text: str, output_path: str = "output/final_video.mp4") -> str:
    logging.info("영상 생성 시작")
    audio_file = generate_audio_from_text(text)
    audio_clip = AudioFileClip(audio_file)
    duration = audio_clip.duration + 2  # 여유 시간 2초 추가
    video_clip = ColorClip(size=(1080,1920), color=(0,0,0), duration=duration).set_audio(audio_clip)
    video_clip.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
    audio_clip.close()
    video_clip.close()
    logging.info(f"영상 생성 완료: {output_path}")
    return output_path
