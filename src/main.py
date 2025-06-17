"""
메인 실행 파일 (최종 수정본)
"""
import logging
from datetime import datetime
import os
from dotenv import load_dotenv
from .content_generator import generate_content
from .voice_generator import generate_voice
from .video_downloader import download_video
from .video_editor import create_video
from .thumbnail_generator import create_thumbnail
from .config import Config

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("youtube_automation.log")
    ]
)
logger = logging.getLogger(__name__)

def cleanup_temp_files():
    """임시 파일 정리"""
    temp_dir = os.path.join(os.getcwd(), "temp")
    for file in os.listdir(temp_dir):
        file_path = os.path.join(temp_dir, file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            logger.error(f"임시 파일 삭제 실패 {file_path}: {e}")

def main():
    """메인 실행 함수"""
    try:
        logger.info("🚀 YouTube 자동화 시스템 시작")
        
        # 1. 환경변수 로드
        load_dotenv()
        
        # 2. 오늘의 주제 설정
        base_topic = "시간 관리의 비밀"  # 실제 사용시에는 주제 리스트에서 랜덤 선택
        
        logger.info(f"📌 오늘의 주제: {base_topic}")
        
        # 3. 콘텐츠 생성
        content = generate_content(base_topic)
        logger.info(f"📝 제목: {content['title']}")
        
        # 4. 음성 생성
        audio_path = generate_voice(content['script'])
        logger.info("🔊 음성 파일 생성 완료")
        
        # 5. 배경 영상 다운로드
        bg_video_path = download_video(content['video_query'])
        logger.info("🎬 배경 영상 다운로드 완료")
        
        # 6. 영상 편집
        output_video_path = os.path.join("output", f"final_video_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp4")
        create_video(bg_video_path, audio_path, output_video_path)
        logger.info("🎥 영상 생성 완료")
        
        # 7. 썸네일 생성
        thumbnail_path = os.path.join("output", "thumbnail.jpg")
        create_thumbnail(content['title'], bg_video_path, thumbnail_path)
        logger.info("🖼️ 썸네일 생성 완료")
        
        # 8. 임시 파일 정리
        cleanup_temp_files()
        
        logger.info("✅ 모든 작업 완료!")
        
    except Exception as e:
        logger.error(f"❌ 오류 발생: {e}")
        raise

if __name__ == "__main__":
    main()
