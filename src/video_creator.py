"""
60초 Shorts 영상 생성 모듈
"""
from moviepy.editor import *
import logging
from .config import Config

logger = logging.getLogger(__name__)

def create_short_video(script, output_path):
    """대본 → 60초 영상 생성"""
    # 1. TTS로 음성 파일 생성 (11Labs 등 활용)
    audio_path = "temp/audio.mp3"
    generate_tts(script["script"], audio_path)  # TTS 모듈 호출
    
    # 2. 영상 클립 조합
    clips = []
    bg_clip = VideoFileClip("assets/shorts_bg.mp4").subclip(0, 60)
    
    # 3. 텍스트 오버레이 추가
    txt_clip = TextClip(
        script["title"],
        fontsize=50,
        color="white",
        font=Config.FONT_PATH,
        stroke_color="black",
        stroke_width=2
    ).set_position(("center", "top")).set_duration(60)
    
    # 4. 최종 영상 렌더링
    final_clip = CompositeVideoClip([bg_clip, txt_clip])
    final_clip = final_clip.set_audio(AudioFileClip(audio_path))
    final_clip.write_videofile(output_path, fps=24, codec="libx264")
