import os
import logging
from datetime import datetime
from src.content_rotator import generate_content
from src.tts_generator import generate_tts
from src.bg_downloader import download_background
from src.video_editor import create_video
from src.youtube_uploader import upload_video
from src.cleanup_manager import cleanup_temp_files

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("💰 유튜브 자동화 시스템 시작")
        
        # 1. 콘텐츠 생성 (AI 로테이션)
        content = generate_content()
        
        # 2. 음성 생성
        audio_path = generate_tts(content['script'])
        
        # 3. 배경 영상 다운로드
        video_path = download_background(content['keywords'])
        
        # 4. 영상 편집
        output_path = create_video(
            video_path=video_path,
            audio_path=audio_path,
            text=content['title'],
            font_path="fonts/Catfont.ttf"
        )
        
        # 5. 유튜브 업로드
        upload_video(
            file_path=output_path,
            title=content['title'],
            description=content['description'],
            keywords=",".join(content['keywords'])
        )
        
    except Exception as e:
        logger.error(f"❌ 오류 발생: {str(e)}")
    finally:
        cleanup_temp_files()

if __name__ == "__main__":
    main()
