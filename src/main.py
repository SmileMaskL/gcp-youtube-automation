import time
import logging
from content_generator import get_trending_topics
from tts_generator import generate_tts
from video_creator import create_video
from youtube_uploader import upload_to_youtube
from config import Config
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    Config.initialize()
    topics = get_trending_topics()
    
    for topic in topics[:5]:  # 상위 5개 주제만 처리
        try:
            logger.info(f"처리 시작: {topic['title']}")
            
            audio_path = generate_tts(topic["script"])
            bg_path = get_background_video(topic["pexel_query"])
            video_path = create_video(topic, audio_path, bg_path)
            
            if upload_to_youtube(video_path, topic["title"]):
                logger.info(f"업로드 성공: {topic['title']}")
            
            time.sleep(random.randint(30, 60))  # 간격 유지
            
        except Exception as e:
            logger.error(f"에러 발생: {e}")
            continue

if __name__ == "__main__":
    main()
