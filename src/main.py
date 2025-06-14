"""
유튜브 자동화 봇 메인 컨트롤러 (2025년 최적화 버전)
"""
import os
import logging
import time
import json
from pathlib import Path
from datetime import datetime, timedelta
import random

from utils import generate_viral_content, text_to_speech, download_video_from_pexels
from video_creator import create_final_video
from youtube_uploader import upload_video
from thumbnail_generator import generate_thumbnail
from content_generator import get_hot_topics

# 로깅 설정
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

class YouTubeAutomation:
    def __init__(self):
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.used_topics = set()
        self.load_used_topics()
        
    def load_used_topics(self):
        if Path("used_topics.json").exists():
            with open("used_topics.json", "r") as f:
                self.used_topics = set(json.load(f))
    
    def save_used_topics(self):
        with open("used_topics.json", "w") as f:
            json.dump(list(self.used_topics), f)
    
    def get_fresh_topic(self):
        """중복되지 않은 새로운 주제 가져오기"""
        max_retries = 5
        for _ in range(max_retries):
            topics = get_hot_topics()
            for topic in topics:
                if topic not in self.used_topics:
                    self.used_topics.add(topic)
                    self.save_used_topics()
                    return topic
            time.sleep(2)
        return random.choice(["부자가 되는 습관", "AI로 돈 버는 법", "성공 비결", "재테크 팁"])

    def run(self):
        logger.info("="*50)
        logger.info("💰 유튜브 수익형 자동화 시스템 시작 💰")
        logger.info("="*50)

        # 1. 새로운 주제 선정
        topic = self.get_fresh_topic()
        logger.info(f"🔥 오늘의 주제: {topic}")

        try:
            # 2. AI로 콘텐츠 생성
            content = generate_viral_content(topic)
            if not content or len(content.get("script", "")) < 50:
                raise ValueError("생성된 대본이 너무 짧습니다.")
            
            title = content["title"]
            script = content["script"]
            hashtags = content["hashtags"]
            
            logger.info(f"📝 생성된 제목: {title}")
            logger.info(f"📜 생성된 대본 길이: {len(script)}자")
            
            # 3. 썸네일 생성
            thumbnail_path = generate_thumbnail(topic)
            logger.info(f"🖼️ 썸네일 생성 완료: {thumbnail_path}")
            
            # 4. 최종 영상 제작
            final_video_path = create_final_video(topic, title, script)
            if not final_video_path:
                raise ValueError("영상 생성 실패")
            
            logger.info(f"🎥 영상 생성 완료: {final_video_path}")
            
            # 5. 유튜브 업로드
            upload_result = upload_video(
                video_path=final_video_path,
                title=f"{title} #shorts",
                description=f"{script}\n\n{' '.join(hashtags)}",
                tags=hashtags,
                privacy_status="public",
                thumbnail_path=thumbnail_path
            )
            
            if upload_result:
                logger.info("✅ 업로드 성공!")
                # 업로드 후 파일 정리
                Path(final_video_path).unlink(missing_ok=True)
                Path(thumbnail_path).unlink(missing_ok=True)
            else:
                logger.error("❌ 업로드 실패")

        except Exception as e:
            logger.error(f"❌ 오류 발생: {str(e)}", exc_info=True)

def main():
    automation = YouTubeAutomation()
    automation.run()

if __name__ == "__main__":
    main()
