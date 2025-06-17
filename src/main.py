"""
YouTube 자동화 메인 시스템 (최종 수정본)
"""
import logging
import sys
import random
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.content_generator import generate_content
from src.tts_generator import text_to_speech
from src.bg_downloader import download_background_video
from src.video_creator import create_video_with_subtitles
from src.thumbnail_generator import create_thumbnail
from src.youtube_uploader import upload_to_youtube

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOGS_DIR / "youtube_automation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_daily_trending_topic():
    """매일 다른 트렌드 주제 선택"""
    topics = [
        "부자가 되는 습관 5가지",
        "성공하는 사람들의 아침 루틴",
        "돈 버는 부업 아이디어 2025",
        "초보자도 할 수 있는 투자 방법",
        "시간 관리의 비밀",
        "생산성을 높이는 방법",
        "스트레스 해소 기술",
        "건강한 삶을 위한 팁",
        "인간관계 개선 방법",
        "자기계발 필수 습관"
    ]
    return random.choice(topics)

def main():
    try:
        logger.info("🚀 YouTube 자동화 시스템 시작")
        
        # 1. 주제 선정
        topic = get_daily_trending_topic()
        logger.info(f"📌 오늘의 주제: {topic}")
        
        # 2. 콘텐츠 생성
        content = generate_content(topic)
        logger.info(f"📝 제목: {content['title']}")
        
        # 3. 음성 생성
        text_to_speech(content['script'], Config.AUDIO_FILE_PATH)
        logger.info(f"🔊 음성 파일 생성 완료")
        
        # 4. 배경 영상 다운로드
        bg_path = download_background_video(content['video_query'])
        logger.info(f"🎬 배경 영상 다운로드 완료")
        
        # 5. 영상 생성 (함수 이름 통일)
        create_video_with_subtitles(
            bg_path,
            Config.AUDIO_FILE_PATH,
            content['script_with_timing'],
            Config.VIDEO_FILE_PATH
        )
        logger.info(f"🎥 영상 생성 완료")
        
        # 6. 썸네일 생성
        create_thumbnail(
            content['title'],
            bg_path,
            Config.THUMBNAIL_FILE_PATH
        )
        logger.info(f"🖼️ 썸네일 생성 완료")
        
        # 7. 유튜브 업로드
        upload_to_youtube(
            Config.VIDEO_FILE_PATH,
            content['title'],
            content['description'],
            content['tags'],
            Config.THUMBNAIL_FILE_PATH
        )
        logger.info("✅ YouTube 업로드 완료!")
        
    except Exception as e:
        logger.error(f"❌ 오류 발생: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    load_dotenv()
    main()
