import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# 프로젝트 루트를 시스템 경로에 추가 (강력한 버전)
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.append(str(project_root))

# 절대 임포트로 통일
from src.content_generator import ShortsGenerator
from src.voice_generator import generate_voice
from src.video_downloader import download_video
from src.video_editor import create_video
from src.thumbnail_generator import create_thumbnail
from src.config import Config

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
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
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
        
        # 2. 콘텐츠 생성기 초기화
        generator = ShortsGenerator()
        
        # 3. 콘텐츠 생성
        contents = generator.generate_daily_contents()
        if not contents:
            raise ValueError("생성된 콘텐츠가 없습니다")
            
        for content in contents:
            logger.info(f"📌 처리 중인 주제: {content['title']}")
            
            # 4. 음성 생성
            audio_path = generate_voice(content['script'])
            logger.info("🔊 음성 파일 생성 완료")
            
            # 5. 배경 영상 다운로드
            bg_video_path = download_video(content['video_query'])
            logger.info("🎬 배경 영상 다운로드 완료")
            
            # 6. 영상 편집
            output_dir = os.path.join("output")
            os.makedirs(output_dir, exist_ok=True)
            output_video_path = os.path.join(output_dir, f"final_video_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp4")
            create_video(bg_video_path, audio_path, output_video_path)
            logger.info("🎥 영상 생성 완료")
            
            # 7. 썸네일 생성
            thumbnail_path = os.path.join(output_dir, "thumbnail.jpg")
            create_thumbnail(content['title'], bg_video_path, thumbnail_path)
            logger.info("🖼️ 썸네일 생성 완료")
        
        # 8. 임시 파일 정리
        cleanup_temp_files()
        
        logger.info("✅ 모든 작업 완료!")
        
    except Exception as e:
        logger.error(f"❌ 오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
