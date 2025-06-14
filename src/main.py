import os
import logging
import sys
import time
from content_generator import generate_content, get_hot_topics
from video_creator import create_video
from youtube_uploader import upload_video

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler(os.path.join(BASE_DIR, "youtube_shorts.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    logger.info("=" * 50)
    logger.info("🎬 유튜브 Shorts 자동 생성 시스템 시작")
    logger.info("=" * 50)

    # 1. 실시간 핫이슈 6개 수집
    topics = get_hot_topics()
    logger.info(f"📢 오늘의 대한민국 핫이슈 {len(topics)}개: {', '.join(topics)}")

    # 2. 환경 변수 확인
    required_envs = [
        "GEMINI_API_KEY",
        "ELEVENLABS_API_KEY",
        "PEXELS_API_KEY",
        "YOUTUBE_OAUTH_CREDENTIALS"]
    missing = [env for env in required_envs if not os.getenv(env)]
    if missing:
        logger.error(f"❌ 필수 환경변수 누락: {', '.join(missing)}")
        return

    # 3. 주제별 영상 생성
    for idx, topic in enumerate(topics):
        logger.info(f"\n🔥 [{idx + 1}/6] 주제 처리 시작: {topic}")
        try:
            # 대본 생성
            script = generate_content(topic)
            if not script or len(script) < 20:
                logger.warning("⚠️ 대본 생성 실패. 다음 주제로 넘어감")
                continue

            # 동영상 생성
            video_path = create_video(script, topic)
            if not video_path or not os.path.exists(video_path):
                logger.error("❌ 동영상 생성 실패")
                continue

            # 업로드
            upload_video(
                video_path=video_path,
                title=f"{topic} 🔥 최신 이슈",
                description=f"{topic} 관련 최신 정보. #Shorts #한국이슈 #실시간뉴스",
                tags=["Shorts", "한국이슈", "실시간뉴스", topic],
                privacy_status="public"
            )

            # 간격 유지
            time.sleep(10)

        except Exception as e:
            logger.error(f"❌ 처리 실패: {str(e)}")

    logger.info("\n✅ 모든 Shorts 생성 및 업로드 완료!")


if __name__ == "__main__":
    main()
