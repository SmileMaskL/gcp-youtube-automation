import logging
from src.config import Config
from src.content_rotator import ContentGenerator
from src.tts_generator import generate_tts
from src.bg_downloader import download_background
from src.video_editor import create_short_video
from src.youtube_uploader import upload_youtube_short

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def produce_daily_shorts():
    try:
        # 1. 콘텐츠 생성
        generator = ContentGenerator()
        content = generator.create_content()
        
        # 2. 음성 생성
        audio_path = generate_tts(
            text=content['script'],
            voice_id=Config.get_voice_id()
        )
        
        # 3. 배경 영상 다운로드
        video_path = download_background(content['video_query'])
        
        # 4. 쇼츠 영상 제작
        output_path = create_short_video(
            video_path=video_path,
            audio_path=audio_path,
            text=content['title'],
            font_path="fonts/Catfont.ttf"
        )
        
        # 5. 유튜브 업로드
        upload_youtube_short(
            file_path=output_path,
            title=content['title'],
            description=content['description']
        )
        
        return True
    except Exception as e:
        logger.error(f"생성 실패: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    for i in range(5):  # 하루 5개 영상 생성
        if produce_daily_shorts():
            logger.info(f"{i+1}번째 쇼츠 생성 성공")
