"""
유튜브 자동화 봇 메인 컨트롤러
- 역할: 전체 프로세스(주제 선정 -> 콘텐츠 생성 -> 영상 제작 -> 업로드)를 순서대로 지휘
"""

import os
import logging
import time
import json
from pathlib import Path

# 각 역할에 맞는 모듈에서 필요한 함수만 가져옵니다.
from utils import generate_viral_content
from video_creator import create_final_video
from youtube_uploader import upload_video # youtube_uploader.py는 이미 있다고 가정

# 로깅 기본 설정
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/youtube_automation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_hot_topics() -> list:
    """수익성 높은 주제 목록을 가져옵니다. (AI 또는 기본 목록)"""
    default_topics = ["부자가 되는 사소한 습관", "AI로 돈 버는 현실적인 방법", "성공한 사람들의 비밀", "절대 하지 말아야 할 재테크", "단기간에 똑똑해지는 법"]
    try:
        # API 키는 utils가 아닌 메인에서 직접 관리하는 것이 더 안전합니다.
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            logger.warning("GEMINI_API_KEY가 없어 기본 주제를 사용합니다.")
            return default_topics
        
        # AI를 활용한 주제 생성은 utils.py에 이미 기능이 있으므로 재사용
        # 여기서는 간단하게 기본 목록을 사용하도록 로직 단순화
        logger.info("기본 수익형 주제 목록을 사용합니다.")
        return default_topics
    except Exception as e:
        logger.error(f"주제 선정 중 오류 발생: {e}")
        return default_topics

def main():
    logger.info("="*50)
    logger.info("💰 유튜브 수익형 자동화 시스템 시작 💰")
    logger.info("="*50)

    # 1. 수익형 주제 목록 가져오기
    topics = get_hot_topics()
    logger.info(f"🔥 오늘의 공략 주제: {', '.join(topics)}")

    # 2. 각 주제에 대해 영상 제작 및 업로드
    for topic in topics:
        try:
            logger.info(f"\n{'='*20} [{topic}] 작업 시작 {'='*20}")
            
            # 2-1. AI로 바이럴 콘텐츠 (제목, 대본) 생성 (from utils.py)
            content = generate_viral_content(topic)
            if not content or len(content.get("script", "")) < 50:
                logger.error("AI가 생성한 대본이 너무 짧거나 유효하지 않아 이 주제를 건너뜁니다.")
                continue

            title = content["title"]
            script = content["script"]
            hashtags = content["hashtags"]
            logger.info(f"📝 생성된 제목: {title}")
            
            # 2-2. 최종 영상 제작 (from video_creator.py)
            final_video_path = create_final_video(topic, title, script)
            
            if not final_video_path:
                logger.error("최종 영상 파일이 생성되지 않았습니다. 이 주제를 건너뜁니다.")
                continue

            # 2-3. 유튜브에 업로드 (from youtube_uploader.py)
            logger.info(f"🚀 '{final_video_path}' 영상을 유튜브에 업로드합니다...")
            upload_video(
                video_path=final_video_path,
                title=f"{title} #shorts",
                description=f"{script}\n\n{' '.join(hashtags)}",
                tags=hashtags,
                privacy_status="private" # 'public'으로 바로 공개하거나 'private'로 초안 저장
            )
            logger.info("✅ 업로드 성공!")

            # 2-4. 임시 파일 정리 및 API 제한 방지를 위한 대기
            os.remove(final_video_path)
            time.sleep(15)

        except Exception as e:
            logger.critical(f"❌ '{topic}' 주제 처리 중 심각한 오류 발생: {e}", exc_info=True)
            continue

    logger.info("\n🎉🎉🎉 모든 작업이 성공적으로 완료되었습니다! 🎉🎉🎉")

if __name__ == "__main__":
    main()
