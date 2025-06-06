import os
import requests
import logging
import tempfile
from moviepy.editor import *
from PIL import Image
import shutil

logger = logging.getLogger(__name__)

# ▼▼▼ 해상도 설정 추가 (기본값 480p)
def create_video(script, output_path, duration=60, resolution="480p"):
    # 해상도 설정
    RESOLUTIONS = {
        "480p": (854, 480),
        "720p": (1280, 720),
        "1080p": (1920, 1080)
    }
    TARGET_SIZE = RESOLUTIONS.get(resolution, (854, 480))
    
    # 1. 배경 이미지 (480p 크기로 리사이즈)
    image_path = download_pexels_image("abstract")
    if image_path:
        img = Image.open(image_path)
        img = img.resize(TARGET_SIZE, Image.LANCZOS)  # ▼▼▼ 핵심 변경!
        img.save(image_path)
        bg_clip = ImageClip(image_path).set_duration(duration)
    else:
        bg_clip = ColorClip(TARGET_SIZE, color=(0,0,0)).set_duration(duration)
    
    # 2. 음성 생성 (60초로 고정)
    audio_path = generate_audio_from_text(script[:500], "EXAVITQu4vr4xnSDxM")
    audio_clip = AudioFileClip(audio_path).subclip(0, min(60, duration))
    
    # 3. 텍스트 생성 (480p에 맞춰 폰트 크기 조정)
    text_clip = TextClip(
        script[:500], 
        fontsize=30 if resolution=="480p" else 50,  # ▼▼▼ 해상도별 크기 조절
        color='white',
        size=(TARGET_SIZE[0]-100, None),
        method='caption'
    ).set_position('center').set_duration(duration)
    
    # 4. 영상 조립
    final_video = CompositeVideoClip([bg_clip, text_clip], size=TARGET_SIZE)
    final_video = final_video.set_audio(audio_clip)
    
    # 5. 출력 (480p)
    final_video.write_videofile(
        output_path,
        fps=24,
        codec='libx264',
        audio_codec='aac',
        threads=4,
        preset='fast'
    )
    return output_path

# 나머지 함수는 동일 (download_pexels_image, generate_audio_from_text 등)
