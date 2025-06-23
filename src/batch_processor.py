import os
import logging
import json
from src.config import get_secret, setup_logging
from src.ai_manager import AIManager
from src.content_curator import ContentCurator
from src.bg_downloader import download_pexels_video
from src.tts_generator import generate_audio
from src.video_creator import create_video
from src.shorts_converter import convert_to_shorts
from src.youtube_utils import YouTubeUploader
from src.error_handler import log_error_and_notify
from src.utils import cleanup_old_files


logger = logging.getLogger(__name__)


def main():
    setup_logging()
    try:
        project_id = os.getenv("GCP_PROJECT_ID")
        bucket_name = os.getenv("GCP_BUCKET_NAME")
        voice_id = os.getenv("ELEVENLABS_VOICE_ID", "uyVNoMrnUku1dZyVEXwD")

        elevenlabs_key = get_secret("ELEVENLABS_API_KEY")
        pexels_key = get_secret("PEXELS_API_KEY")
        news_key = get_secret("NEWS_API_KEY")
        youtube_creds = json.loads(get_secret("YOUTUBE_OAUTH_CREDENTIALS"))

        ai_manager = AIManager()
        cleanup_old_files(bucket_name, hours_to_keep=24)

        curator = ContentCurator(news_key)
        topics = curator.get_hot_topics(num_topics=2)
        
        for topic in topics:
            try:
                process_video(
                    topic=topic,
                    project_id=project_id,
                    bucket_name=bucket_name,
                    elevenlabs_key=elevenlabs_key,
                    pexels_key=pexels_key,
                    voice_id=voice_id,
                    youtube_creds=youtube_creds,
                    ai_manager=ai_manager
                )
            except Exception as e:
                log_error_and_notify(
                    f"Topic {topic} processing failed: {str(e)}"
                )

    except Exception as e:
        log_error_and_notify(f"Main pipeline failed: {str(e)}")


def process_video(topic, project_id, bucket_name, elevenlabs_key, 
                  pexels_key, voice_id, youtube_creds, ai_manager):
    logger.info(f"Processing topic: {topic}")
    script = ai_manager.generate_script(topic)
    
    audio_path = "/tmp/audio.mp3"
    generate_audio(script, audio_path, elevenlabs_key, voice_id)
    
    video_url = download_pexels_video(pexels_key, topic)
    output_path = "/tmp/final.mp4"
    create_video(video_url, audio_path, output_path)
    
    shorts_path = "/tmp/shorts.mp4"
    convert_to_shorts(output_path, shorts_path)
    
    uploader = YouTubeUploader(youtube_creds)
    uploader.upload_video(
        video_path=shorts_path,
        title=f"{topic} 최신 정보 🚀",
        description=(
            f"{topic}에 관한 최신 업데이트입니다. "
            f"#shorts #{topic.replace(' ', '')}"
        ),
        tags=["shorts", "자동생성", topic]
    )


if __name__ == "__main__":
    main()
