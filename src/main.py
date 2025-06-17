import sys
import time
import random
import logging
from datetime import datetime
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))

# 절대 경로로 임포트 (상대 경로 대신)
from src.config import Config
from src.content_generator import get_trending_topics
from src.tts_generator import generate_tts
from src.video_creator import create_video
from src.youtube_uploader import upload_to_youtube
from src.bg_downloader import download_background_video

# 로거 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOGS_DIR / 'youtube_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def cleanup_old_files(days=7):
    """오래된 파일 정리"""
    from datetime import datetime, timedelta
    cutoff = datetime.now() - timedelta(days=days)
    deleted_files = 0

    for dir_path in [Config.TEMP_DIR, Config.OUTPUT_DIR]:
        for f in dir_path.glob('*'):
            if f.is_file() and datetime.fromtimestamp(f.stat().st_mtime) < cutoff:
                try:
                    f.unlink()
                    deleted_files += 1
                except Exception as e:
                    logger.warning(f"파일 삭제 실패: {f} - {e}")
                    
    logger.info(f"정리 완료: {deleted_files}개의 오래된 파일 삭제")

def main():
    """메인 실행 함수"""
    try:
        logger.info("="*50)
        logger.info("YouTube 자동화 시스템 시작")
        logger.info(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*50)
        
        # 1. 트렌딩 주제 가져오기
        topics = get_trending_topics()
        logger.info(f"생성된 주제 수: {len(topics)}")
        
        # 2. 최대 5개 주제 처리
        for i, topic in enumerate(topics[:5]):
            try:
                logger.info(f"\n[진행 중] {i+1}/{min(5, len(topics))} - {topic['title']}")
                
                # 3. 음성 생성
                audio_path = generate_tts(topic["script"])
                logger.info(f"음성 파일 생성: {audio_path}")
                
                # 4. 배경 영상 다운로드
                bg_path = download_background_video(topic["pexel_query"])
                logger.info(f"배경 영상 다운로드: {bg_path}")
                
                # 5. 영상 생성
                video_path = create_video(topic, audio_path, bg_path)
                logger.info(f"영상 생성 완료: {video_path}")
                
                # 6. YouTube 업로드
                if upload_to_youtube(video_path, topic["title"]):
                    logger.info(f"업로드 성공: {topic['title']}")
                else:
                    logger.warning(f"업로드 실패: {topic['title']}")
                
                # 7. 간격 유지 (30-60초)
                if i < len(topics[:5]) - 1:
                    wait_time = random.randint(30, 60)
                    logger.info(f"다음 작업까지 {wait_time}초 대기...")
                    time.sleep(wait_time)
                    
            except Exception as e:
                logger.error(f"주제 처리 중 오류 발생: {e}", exc_info=True)
                continue
                
        # 8. 오래된 파일 정리
        cleanup_old_files()
        
    except Exception as e:
        logger.error(f"시스템 오류 발생: {e}", exc_info=True)
    finally:
        logger.info("="*50)
        logger.info("YouTube 자동화 시스템 종료")
        logger.info("="*50)

if __name__ == "__main__":
    main()
