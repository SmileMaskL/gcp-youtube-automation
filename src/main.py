# src/main.py (수정 버전)

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
        logging.FileHandler(os.path.join(BASE_DIR, "youtube_automation.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    logger.info("="*50)
    logger.info("🎬 유튜브 자동화 시스템 시작 (Shorts 전용)")
    logger.info("="*50)

    # 재생목록 ID 설정 (사용자가 변경해야 함)
    MY_PLAYLIST_ID = "PLxxxxxxxxxxxxxxxxxx"  # <--- 사용자의 재생목록 ID로 변경

    # 주제 자동 수집
    topics = get_hot_topics()
    logger.info(f"오늘의 대한민국 핫이슈 {len(topics)}개: {topics}")

    for idx, topic in enumerate(topics):
        logger.info(f"\n🔥 [{idx+1}/{len(topics)}] 주제 처리 시작: {topic}")
        try:
            script = generate_content(topic)
            if "기본 스크립트" in script:
                logger.error(f"대본 생성에 실패하여 다음 주제로 넘어갑니다: {topic}")
                continue
            
            video_path = create_video(script, topic)
            if not video_path:
                logger.error(f"동영상 생성에 실패하여 다음 주제로 넘어갑니다: {topic}")
                continue

            description = f"AI가 생성한 '{topic}'에 대한 영상입니다.\n\n#AI #자동화 #유튜브봇 #자기계발 #꿀팁 #shorts"
            tags = ["AI", "자동화", "유튜브봇", "shorts", topic.split(',')[0].strip()]
            
            upload_video(
                video_path=video_path,
                title=topic,
                description=description,
                tags=tags,
                playlist_id=MY_PLAYLIST_ID,    # '유익한 정보' 재생목록에 추가
                privacy_status="public"       # '공개' 상태로 업로드
            )
            
            time.sleep(5)

        except Exception as e:
            logger.error(f"❌ '{topic}' 처리 중 예상치 못한 오류 발생: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

    logger.info("\n✨ 모든 수작업 없는 완전 자동화 작업이 완료되었습니다. ✨")

if __name__ == "__main__":
    main()
