# src/main.py (전체 코드)

import os
import logging
import sys
import time

# main.py 파일의 위치를 기준으로 경로를 설정합니다.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# 🔥 진짜 모듈들을 임포트합니다!
from content_generator import generate_content
from video_creator import create_video
from youtube_uploader import upload_video

# 로깅 설정
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
    logger.info("🎬 유튜브 자동화 시스템 시작 (업로더 장착 최종 버전)")
    logger.info("="*50)

    # 🔥 2025년 6월, 수익 극대화를 위한 최신 트렌드 주제
    topics = [
        "클로드 3.5 소네트, GPT-4o보다 정말 똑똑할까? (실사용 비교)",
        "Suno V3, 단 1분만에 노래 만드는 AI (저작권 걱정 없는 음원 만들기)",
        "무료 AI 영상 제작 툴 'Luma Dream Machine' 사용법 총정리",
        "월 500만원 버는 AI 자동화 부업, 지금 당장 시작해야 하는 이유",
        "평생 무료로 쓰는 구글 클라우드, 2025년 최신 신청 방법"
    ]

    for idx, topic in enumerate(topics):
        logger.info(f"\n🔥 [{idx+1}/{len(topics)}] 주제 처리 시작: {topic}")
        try:
            # 1. AI가 대본 생성
            script = generate_content(topic)
            if "실패" in script:
                logger.error(f"대본 생성에 실패하여 다음 주제로 넘어갑니다: {topic}")
                continue
            
            # 2. 동영상 생성
            video_path = create_video(script, topic)
            if not video_path:
                logger.error(f"동영상 생성에 실패하여 다음 주제로 넘어갑니다: {topic}")
                continue

            # 3. 🔥 진짜 유튜브 업로드 실행!
            description = f"AI가 생성한 '{topic}'에 대한 영상입니다.\n\n#AI #자동화 #유튜브봇"
            tags = ["AI", "자동화", "유튜브봇", topic.split(',')[0]]
            upload_video(video_path, topic, description, tags)
            
            # 작업 사이에 약간의 딜레이를 주어 시스템 안정성 확보
            time.sleep(5)

        except Exception as e:
            logger.error(f"❌ '{topic}' 처리 중 예상치 못한 오류 발생: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

    logger.info("\n✨ 모든 작업이 완료되었습니다. ✨")

if __name__ == "__main__":
    main()
