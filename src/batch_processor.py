import os
import logging
from datetime import datetime
from src.content_rotator import ContentGenerator
from src.tts_generator import generate_tts
from src.bg_downloader import download_background
from src.video_editor import create_video
from src.youtube_uploader import upload_video
from src.cleanup_manager import cleanup_temp_files

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("🚀 자동화 시스템 시작")
        
        # 1. 콘텐츠 생성
        generator = ContentGenerator()
        content = generator.create_content()
        
        # 2. 음성 생성
        audio_path = generate_tts(
            text=content['script'],
            voice_id="uyVNoMrnUku1dZyVEXwD"  # 안나 킴 목소리
        )
        
        # 3. 배경 영상 다운로드
        video_path = download_background(
            query=content['video_query'],
            api_key=os.getenv("PEXELS_API_KEY")
        )
        
        # 4. 영상 제작
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
            description=f"{content['script']}\n\n#Shorts #자동생성",
            keywords=",".join(content['keywords']),
            credentials=os.getenv("YOUTUBE_CREDENTIALS")
        )
        
    except Exception as e:
        logger.error(f"❌ 심각한 오류: {str(e)}")
    finally:
        cleanup_temp_files()

if __name__ == "__main__":
    main()
