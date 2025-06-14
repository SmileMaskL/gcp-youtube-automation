"""
유튜브 자동화 메인 시스템 (무조건 실행되는 버전)
"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from utils import (
    generate_viral_content,
    text_to_speech,
    download_video_from_pexels,
    Config
)
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip

# 초기 설정
load_dotenv()
Config.ensure_temp_dir()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_video(script: str, bg_video_path: str, audio_path: str) -> str:
    """영상 생성 (실패 시 기본 영상)"""
    try:
        video_clip = VideoFileClip(bg_video_path).subclip(0, 60)
        audio_clip = AudioFileClip(audio_path)
        
        # 간단한 텍스트 추가 (ImageMagick 필요 없음)
        txt_clip = TextClip(
            script[:100],  # 처음 100자만 표시
            fontsize=50,
            color='white',
            size=(900, 1600),
            method='caption'
        ).set_duration(audio_clip.duration)
        
        final_clip = CompositeVideoClip([video_clip, txt_clip])
        final_clip = final_clip.set_audio(audio_clip)
        
        output_path = "output/final_video.mp4"
        Path("output").mkdir(exist_ok=True)
        final_clip.write_videofile(output_path, fps=24, threads=4)
        return output_path
    except Exception as e:
        logger.error(f"영상 생성 실패: {e}")
        return bg_video_path  # 원본 영상 반환

def main():
    logger.info("🚀 시스템 시작")
    
    # 1. 콘텐츠 생성
    topic = "재테크"  # 실제 사용시에는 동적 주제 선정
    content = generate_viral_content(topic)
    logger.info(f"제목: {content['title']}")
    
    # 2. 음성 생성
    audio_path = text_to_speech(content['script'], "temp/audio.mp3")
    
    # 3. 영상 다운로드
    video_path = download_video_from_pexels(topic)
    
    # 4. 최종 영상 생성
    final_path = create_video(content['script'], video_path, audio_path)
    logger.info(f"✅ 최종 영상: {final_path}")

if __name__ == "__main__":
    main()
