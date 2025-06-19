import logging
from src.ai_rotation import ai_manager
from src.content_generator import ContentGenerator
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
        logger.info("콘텐츠 생성 시작")
        api_key, ai_type = ai_manager.get_ai_key()
        generator = ContentGenerator(api_key=api_key, ai_type=ai_type)
        topic = generator.get_daily_topic()
        script = generator.generate_script(topic)
        
        # 2. 영상 생성
        logger.info("영상 생성 중")
        video_path = create_video(
            script=script,
            font_path="fonts/Catfont.ttf",
            voice_id=os.getenv("ELEVENLABS_VOICE_ID", "uyVNoMrnUku1dZyVEXwD")  # 안나 킴 목소리
        )
        
        # 3. 유튜브 업로드
        logger.info("유튜브 업로드 중")
        creds = Config.get_youtube_creds()
        uploader = YouTubeUploader(creds)
        response = uploader.upload_video(
            file_path=video_path,
            title=f"{topic} #shorts",
            description=f"자동 생성된 Shorts 영상입니다. 주제: {topic}"
        )
        
        logger.info(f"업로드 성공! Video ID: {response.get('id')}")
    except Exception as e:
        logger.error(f"배치 처리 오류: {str(e)}")
        raise

if __name__ == "__main__":
    import os
    main()
