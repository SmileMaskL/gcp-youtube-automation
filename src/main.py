import time
import random
import logging
import uuid
import requests
from content_generator import get_trending_topics
from tts_generator import generate_tts
from video_creator import create_video
from youtube_uploader import upload_to_youtube
from config import Config  # Config 클래스 import 추가

# 로거 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('youtube_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_background_video(query):
    """Pexels에서 배경 영상 다운로드"""
    video_path = Config.TEMP_DIR / f"bg_{uuid.uuid4()}.mp4"
    try:
        headers = {"Authorization": Config.get_api_key("PEXELS_API_KEY")}
        response = requests.get(
            f"https://api.pexels.com/videos/search?query={query}&per_page=5",
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        
        videos = response.json().get("videos", [])
        if not videos:
            raise ValueError("검색 결과 없음")
            
        video = random.choice(videos)
        video_file = next(
            (f for f in video["video_files"] if f.get("width") == Config.SHORTS_WIDTH),
            video["video_files"][0]
        )
        
        with requests.get(video_file["link"], stream=True) as r:
            r.raise_for_status()
            with open(video_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        
        logger.info(f"배경 영상 다운로드 성공: {video_path}")
        return video_path
        
    except Exception as e:
        logger.error(f"배경 영상 다운로드 실패: {e}")
        raise

def main():
    """메인 실행 함수"""
    try:
        logger.info("YouTube 자동화 시스템 시작")
        
        # 트렌딩 주제 가져오기
        topics = get_trending_topics()
        logger.info(f"생성된 주제 수: {len(topics)}")
        
        # 상위 5개 주제 처리
        for i, topic in enumerate(topics[:5]):
            try:
                logger.info(f"[{i+1}/5] 처리 시작: {topic['title']}")
                
                # 음성 생성
                audio_path = generate_tts(topic["script"])
                logger.info(f"음성 생성 완료: {audio_path}")
                
                # 배경 영상 다운로드
                bg_path = get_background_video(topic["pexel_query"])
                logger.info(f"배경 영상 다운로드 완료: {bg_path}")
                
                # 영상 생성
                video_path = create_video(topic, audio_path, bg_path)
                logger.info(f"영상 생성 완료: {video_path}")
                
                # YouTube 업로드
                if upload_to_youtube(video_path, topic["title"]):
                    logger.info(f"성공적으로 업로드 완료: {topic['title']}")
                else:
                    logger.warning(f"업로드 실패: {topic['title']}")
                
                # 간격 유지 (30-60초)
                wait_time = random.randint(30, 60)
                if i < 4:
                    logger.info(f"다음 작업까지 {wait_time}초 대기...")
                    time.sleep(wait_time)
                    
            except Exception as e:
                logger.error(f"주제 처리 중 오류 발생: {e}", exc_info=True)
                continue
                
    except Exception as e:
        logger.error(f"시스템 오류 발생: {e}", exc_info=True)
    finally:
        logger.info("YouTube 자동화 시스템 종료")

if __name__ == "__main__":
    main()
