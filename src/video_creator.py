"""
60초 YouTube Shorts 영상 생성 모듈
"""
from moviepy.editor import *
import os
from .config import Config
import logging

logger = logging.getLogger(__name__)

def create_short_video(content, output_path="output/final.mp4"):
    """대본 → 60초 세로 영상 생성"""
    try:
        # 1. 배경 영상 준비 (세로 9:16 비율)
        bg_clip = VideoFileClip("assets/shorts_bg.mp4").subclip(0, 60)
        
        # 2. 텍스트 오버레이 생성
        txt_clip = TextClip(
            content["title"],
            fontsize=45,
            color="white",
            font=Config.FONT_PATH,
            size=(bg_clip.w*0.9, None),
            method="caption",
            align="center",
            stroke_color="black",
            stroke_width=2
        ).set_position(("center", "top")).set_duration(60)
        
        # 3. 음성 합성 (TTS 모듈 연동)
        audio_path = "temp/audio.mp3"
        generate_tts(content["script"], audio_path)  # 별도 TTS 모듈 호출
        
        # 4. 최종 영상 렌더링
        final_clip = CompositeVideoClip([bg_clip, txt_clip])
        final_clip = final_clip.set_audio(AudioFileClip(audio_path))
        final_clip.write_videofile(
            output_path,
            fps=24,
            codec="libx264",
            preset="fast",
            threads=4
        )
        return output_path
        
    except Exception as e:
        logger.error(f"영상 생성 실패: {e}")
        raise
