import logging
from src.ai_rotation import ai_manager
from src.content_generator import generate_content
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
        topic, script = generate_content()
        
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
