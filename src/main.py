# src/main.py (전체 코드)

import os
import json
import random
import logging
import sys
import time

# main.py 파일의 위치를 기준으로 경로를 설정합니다.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# 🔥 이제 모듈 임포트가 안정적으로 작동합니다.
from video_creator import create_video
# from content_generator import generate_content # 실제 파일이 있다면 주석 해제

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

def load_environment():
    # .env 파일이 있다면 로드 (로컬 테스트용)
    from dotenv import load_dotenv
    dotenv_path = os.path.join(os.path.dirname(BASE_DIR), '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path=dotenv_path)
        logger.info(".env 파일에서 환경변수를 로드했습니다.")
    else:
        logger.info(".env 파일을 찾을 수 없습니다. GitHub Secrets를 사용합니다.")
    # (이하 환경변수 로드 로직은 이전과 동일...)
    return True # 단순화

def main():
    logger.info("="*50)
    logger.info("🎬 유튜브 자동화 시스템 시작 (최종 안정화 버전)")
    logger.info("="*50)

    load_environment()

    # 🔥 2025년 6월 13일, 금요일 오후 최신 트렌드 주제
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
            # 1. 대본 생성 (실제 content_generator가 없으므로 예시 스크립트 사용)
            logger.info("대본 생성을 시작합니다...")
            script = f"안녕하세요, 여러분! 오늘은 정말 핫한 주제, '{topic}'에 대해 쉽고 빠르게 알려드리겠습니다. 많은 분들이 궁금해하시는 내용, 지금 바로 시작합니다!"
            # 실제 사용 시: script = generate_content(topic)
            logger.info("✅ 대본 생성 완료")
            
            # 2. 동영상 생성
            logger.info("동영상 생성을 시작합니다...")
            video_path = create_video(script, topic)
            if not video_path:
                logger.error(f"❌ 동영상 생성에 실패하여 다음 주제로 넘어갑니다: {topic}")
                continue

            logger.info(f"🎉 최종 성공! '{topic}' 영상이 생성되었습니다.")
            logger.info(f"--> 파일 경로: {video_path}")
            
            # 작업 사이에 약간의 딜레이를 주어 시스템 안정성 확보
            time.sleep(5)

        except Exception as e:
            logger.error(f"❌ '{topic}' 처리 중 예상치 못한 오류 발생: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

    logger.info("\n✨ 모든 작업이 완료되었습니다. ✨")

if __name__ == "__main__":
    main()
