import logging
from src.ai_rotation import ai_manager
from src.content_generator import ContentGenerator  # ✅ 수정
from src.video_creator import create_video
from src.youtube_uploader import YouTubeUploader
from src.config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/youtube_shorts.log'
)
logger = logging.getLogger(__name__)

def main():
    try:
        # 1. 콘텐츠 생성
        logger.info("Starting content generation")
        api_key, ai_type = ai_manager.get_next_key()  # ✅ 키 로테이션
        generator = ContentGenerator(api_key=api_key, ai_type=ai_type)  # ✅ 생성자
        topic = generator.get_daily_topic()  # ✅ 주제 선정
        script = generator.generate_script(topic)  # ✅ 스크립트 생성
        
        # 2. 영상 생성
        logger.info("Creating video")
        video_path = create_video(script, "fonts/Catfont.ttf")
        
        # 3. 유튜브 업로드
        logger.info("Uploading to YouTube")
        creds = Config.get_youtube_creds()
        uploader = YouTubeUploader(creds)
        response = uploader.upload_video(
            file_path=video_path,
            title=f"{topic} #shorts",
            description=f"자동 생성된 Shorts 영상입니다. {topic}에 관한 내용입니다."
        )
        
        logger.info(f"Upload successful! Video ID: {response.get('id')}")
    except Exception as e:
        logger.error(f"Error in batch processing: {str(e)}")
        raise

if __name__ == "__main__":
    main()
