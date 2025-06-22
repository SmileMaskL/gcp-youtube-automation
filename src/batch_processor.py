import logging
from src.config import Config
from src.ai_manager import AIManager
from src.video_creator import create_short_video
from src.youtube_uploader import upload_video

logger = logging.getLogger(__name__)

def main():
    config = Config()
    ai_manager = AIManager(config)
    
    # 콘텐츠 생성
    content = ai_manager.generate_content("오늘의 트렌드")
    
    # 비디오 생성
    video_path = create_short_video(
        background_path="assets/background.mp4",
        audio_path="temp/audio.mp3",
        output_path="output/final.mp4"
    )
    
    # YouTube 업로드
    upload_video(
        video_path=video_path,
        title="자동 생성 콘텐츠",
        description="AI가 생성한 콘텐츠",
        tags=["shorts", "AI"]
    )

if __name__ == "__main__":
    main()
