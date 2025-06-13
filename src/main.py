# src/main.py (전체 코드)

import os
import logging
import sys
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from content_generator import generate_content
from video_creator import create_video
from youtube_uploader import upload_video

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
    logger.info("🎬 유튜브 자동화 시스템 시작 (최종 자동화 완성 버전)")
    logger.info("="*50)

    # 🔥 여기에 1단계에서 찾은 '유익한 정보' 재생목록 ID를 붙여넣으세요!
    MY_PLAYLIST_ID = "PLxxxxxxxxxxxxxxxxxx" # <--- 이 부분을 나의 재생목록 ID로 바꾸세요!

    # 2025년 6월 13일, 수익 극대화를 위한 최신 트렌드 주제
    topics = [
        "클로드 3.5 소네트, GPT-4o보다 정말 똑똑할까? (실사용 비교)",
        "Suno V3, 단 1분만에 노래 만드는 AI (저작권 걱정 없는 음원 만들기)",
        "무료 AI 영상 제작 툴 'Luma Dream Machine' 사용법 총정리",
        "월 500만원 버는 AI 자동화 부업, 지금 당장 시작해야 하는 이유",
        "평생 무료로 쓰는 구글 클라우드, 2025년 최신 신청 방법"
    ]

    if MY_PLAYLIST_ID == "PLCSyGdRKPP9EdD1hNyNOWXVLcNPm8D8aJ":
        logger.warning("⚠️ 경고: main.py 파일의 'MY_PLAYLIST_ID'를 실제 값으로 변경해주세요. 재생목록에 추가되지 않습니다.")

    for idx, topic in enumerate(topics):
        logger.info(f"\n🔥 [{idx+1}/{len(topics)}] 주제 처리 시작: {topic}")
        try:
            script = generate_content(topic)
            if "실패" in script:
                logger.error(f"대본 생성에 실패하여 다음 주제로 넘어갑니다: {topic}")
                continue
            
            video_path = create_video(script, topic)
            if not video_path:
                logger.error(f"동영상 생성에 실패하여 다음 주제로 넘어갑니다: {topic}")
                continue

            # 🔥 업그레이드된 업로더에게 모든 명령을 내립니다!
            description = f"AI가 생성한 '{topic}'에 대한 영상입니다.\n\n#AI #자동화 #유튜브봇 #자기계발 #꿀팁"
            tags = ["AI", "자동화", "유튜브봇", topic.split(',')[0].strip()]
            
            upload_video(
                video_path=video_path,
                title=topic,
                description=description,
                tags=tags,
                playlist_id=MY_PLAYLIST_ID,    # <-- '유익한 정보' 재생목록에 추가
                privacy_status="public"       # <-- '공개' 상태로 바로 업로드
            )
            
            time.sleep(5)

        except Exception as e:
            logger.error(f"❌ '{topic}' 처리 중 예상치 못한 오류 발생: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

    logger.info("\n✨ 모든 수작업 없는 완전 자동화 작업이 완료되었습니다. ✨")

if __name__ == "__main__":
    main()
