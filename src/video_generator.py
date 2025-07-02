# src/video_generator.py

import logging
from moviepy.editor import ImageClip, AudioFileClip

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def create_video_from_images_and_audio(images, audio_path, output_path):
    """
    단일 이미지 → 오디오 길이만큼 동영상 생성
    """
    try:
        audio = AudioFileClip(audio_path)
        duration = audio.duration

        clip = ImageClip(images[0]).set_duration(duration).set_audio(audio)
        clip = clip.resize(height=1920).crop(x_center=clip.w/2, width=1080, height=1920)
        clip.write_videofile(output_path, fps=30)
        logger.info(f"✅ Video saved to '{output_path}'")
    except Exception as e:
        logger.error(f"❌ Video 생성 실패: {e}")
        raise
