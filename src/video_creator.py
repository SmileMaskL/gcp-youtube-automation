import os
import uuid
from moviepy.editor import *
from utils import (
    text_to_speech,
    download_video_from_pexels,
    add_text_to_clip,
    Config
)
import logging

logger = logging.getLogger(__name__)

def create_video(script: str, topic: str) -> str:
    """수익형 영상 생성 (전체 프로세스 통합)"""
    try:
        logger.info("🎬 영상 생성 시작")
        
        # 1. 배경 영상 다운로드
        video_path = download_video_from_pexels(topic)
        if not os.path.exists(video_path):
            raise FileNotFoundError("영상 다운로드 실패")

        # 2. 음성 생성
        audio_path = text_to_speech(script)
        
        # 3. 영상+음성 합성
        video_clip = VideoFileClip(video_path)
        audio_clip = AudioFileClip(audio_path)
        
        # 영상 길이 조정
        if video_clip.duration < audio_clip.duration:
            video_clip = video_clip.loop(duration=audio_clip.duration)
        else:
            video_clip = video_clip.subclip(0, audio_clip.duration)

        final_clip = video_clip.set_audio(audio_clip)
        
        # 4. 텍스트 추가
        output_path = f"output/{uuid.uuid4()}.mp4"
        os.makedirs("output", exist_ok=True)
        add_text_to_clip(final_clip.filename, script, output_path)

        return output_path

    except Exception as e:
        logger.error(f"영상 생성 실패: {str(e)}")
        return None
