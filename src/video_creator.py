import logging
import os
import random
import time
from moviepy.editor import (
    VideoFileClip, AudioFileClip, CompositeVideoClip,
    TextClip, ColorClip, ImageClip
)
from elevenlabs import ElevenLabs
from src.config import load_config

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 상수 설정
MAX_SHORTS_DURATION = 58
OUTPUT_DIR = "output"

# ElevenLabs 클라이언트 초기화
config = load_config()
client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY") or config.get("ELEVENLABS_API_KEY"))

def download_background_video():
    dummy_video_path = os.path.join(OUTPUT_DIR, "dummy_bg.mp4")
    if not os.path.exists(dummy_video_path):
        try:
            clip = ColorClip(size=(1080, 1920), color=(0, 0, 0), duration=60)
            clip.write_videofile(dummy_video_path, fps=24, logger=None)
            logging.info(f"Created dummy background video: {dummy_video_path}")
        except Exception as e:
            logging.error(f"Failed to create dummy background video: {e}")
            return None
    return dummy_video_path

def generate_audio(text, config):
    voice_id = config.get("ELEVENLABS_VOICE_ID")
    if not client or not voice_id:
        logging.error("ElevenLabs API 키나 Voice ID가 설정되지 않았습니다.")
        return None

    try:
        audio = client.generate(
            text=text,
            voice=voice_id,
            model="eleven_multilingual_v2"
        )
        audio_path = os.path.join(OUTPUT_DIR, f"audio_{random.randint(1000,9999)}.mp3")
        client.save(audio, audio_path)
        logging.info(f"🎤 Audio saved: {audio_path}")
        return audio_path
    except Exception as e:
        logging.error(f"Audio 생성 오류: {e}")
        return None

def generate_thumbnail(video_path, content_title, output_dir):
    thumbnail_path = os.path.join(output_dir, "thumbnail.jpg")
    try:
        clip = VideoFileClip(video_path)
        clip.save_frame(thumbnail_path, t=clip.duration / 2)

        if content_title:
            try:
                img_clip = ImageClip(thumbnail_path)
                txt_clip = TextClip(
                    content_title, fontsize=70, color='white',
                    font=config.get("FONT_PATH"),
                    stroke_color='black', stroke_width=3,
                    size=(img_clip.w * 0.8, None)
                ).set_position(("center", "center"))

                final_thumb = CompositeVideoClip([img_clip.set_duration(1), txt_clip.set_duration(1)])
                final_thumb.save_frame(thumbnail_path, t=0)
                logging.info(f"썸네일 생성됨: {thumbnail_path}")
            except Exception as text_e:
                logging.warning(f"텍스트 추가 실패: {text_e}")

        return thumbnail_path
    except Exception as e:
        logging.error(f"썸네일 생성 실패: {e}")
        return None

def create_video(content, config):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    script = content.get("script")
    title = content.get("title")
    if not script:
        logging.error("스크립트가 비어 있어 영상을 생성할 수 없습니다.")
        return None

    audio_path = generate_audio(script, config)
    if not audio_path:
        return None

    audio_clip = AudioFileClip(audio_path)
    audio_duration = audio_clip.duration
    target_video_duration = min(audio_duration + 2, MAX_SHORTS_DURATION)

    bg_video_path = download_background_video()
    if not bg_video_path or not os.path.exists(bg_video_path):
        logging.error("배경 영상이 유효하지 않습니다.")
        audio_clip.close()
        return None

    try:
        video_clip = VideoFileClip(bg_video_path)
        if video_clip.w / video_clip.h != 9 / 16:
            video_clip = video_clip.resize(newsize=(1080, 1920))

        if video_clip.duration < target_video_duration:
            video_clip = video_clip.loop(duration=target_video_duration)
        else:
            video_clip = video_clip.subclip(0, target_video_duration)

        final_clip = video_clip.set_audio(audio_clip)

        text_clip = TextClip(
            script, fontsize=60, color='white',
            font=config.get("FONT_PATH"),
            stroke_color='black', stroke_width=2,
            size=(final_clip.w * 0.9, None), method='caption'
        ).set_duration(final_clip.duration).set_position(('center', 'center'))

        final_clip = CompositeVideoClip([final_clip, text_clip])

        output_video_path = os.path.join(OUTPUT_DIR, f"youtube_shorts_{int(time.time())}.mp4")
        final_clip.write_videofile(output_video_path, fps=24, codec='libx264', audio_codec='aac', bitrate="5000k", logger=None)
        logging.info(f"🎬 영상 렌더링 완료: {output_video_path}")

        thumbnail_path = generate_thumbnail(output_video_path, title, OUTPUT_DIR)
        if thumbnail_path:
            content["thumbnail_path"] = thumbnail_path

        audio_clip.close()
        video_clip.close()
        final_clip.close()

        os.remove(audio_path)

        return output_video_path
    except Exception as e:
        logging.error(f"영상 생성 중 오류 발생: {e}")
        return None
