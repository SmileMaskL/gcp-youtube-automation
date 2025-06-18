import os
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    try:
        from src.config import Config
        from src.content_generator import ShortsGenerator
        from src.tts_generator import text_to_speech
        from src.bg_downloader import download_background_video
        from src.video_editor import create_video
        from src.thumbnail_generator import create_thumbnail
        from src.youtube_uploader import upload_to_youtube

        # 환경변수 로드
        load_dotenv()
        Config.ensure_directories()

        logger.info("=" * 50)
        logger.info("💰 유튜브 자동화 배치 시스템 시작 💰")
        logger.info("=" * 50)

        generator = ShortsGenerator()
        contents = generator.generate_daily_contents()
        
        for content in contents:
            try:
                logger.info(f"📌 주제: {content['title']}")

                # 오디오 생성
                audio_path = Config.TEMP_DIR / "output_audio.mp3"
                text_to_speech(content['script'], str(audio_path))

                # 배경 영상 다운로드
                bg_video = download_background_video(content['video_query'])
                
                # 영상 생성
                output_vid = Config.OUTPUT_DIR / f"final_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp4"
                create_video(str(bg_video), str(audio_path), str(output_vid))

                # 썸네일 생성
                thumbnail = Config.OUTPUT_DIR / "thumbnail.jpg"
                create_thumbnail(content['title'], str(bg_video), str(thumbnail))

                # YouTube 업로드
                if upload_to_youtube(str(output_vid), content['title']):
                    logger.info(f"✅ 업로드 완료: {content['title']}")

            except Exception as e:
                logger.error(f"❌ 콘텐츠 처리 중 오류: {e}", exc_info=True)
                continue

    except Exception as e:
        logger.error(f"❌ 시스템 전체 오류: {e}", exc_info=True)
        raise
    finally:
        from src.cleanup_manager import cleanup_temp_files
        cleanup_temp_files()

if __name__ == "__main__":
    main()
