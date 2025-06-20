import os
import logging
import json
from datetime import datetime
from src.config import get_secret, setup_logging
from src.ai_manager import AIManager
from src.content_curator import ContentCurator
from src.bg_downloader import download_pexels_video
from src.tts_generator import generate_audio
from src.video_creator import create_video
from src.shorts_converter import convert_to_shorts
from src.youtube_utils import YouTubeUploader
from src.error_handler import log_error_and_notify
from src.utils import upload_to_gcs, cleanup_old_files
복사
from src.batch_processor import main

if __name__ == "__main__":
    main()

setup_logging()
logger = logging.getLogger(__name__)

def main():
    try:
        # 환경 변수 로드
        project_id = os.getenv("GCP_PROJECT_ID")
        bucket_name = os.getenv("GCP_BUCKET_NAME")
        voice_id = os.getenv("ELEVENLABS_VOICE_ID", "uyVNoMrnUku1dZyVEXwD")

        # API 키 로드
        elevenlabs_key = get_secret("ELEVENLABS_API_KEY")
        pexels_key = get_secret("PEXELS_API_KEY")
        news_key = get_secret("NEWS_API_KEY")
        youtube_creds = json.loads(get_secret("YOUTUBE_OAUTH_CREDENTIALS"))

        # AI 매니저 초기화 (10개 키 로테이션)
        ai_manager = AIManager()

        # 1. 오래된 파일 정리
        cleanup_old_files(bucket_name, hours_to_keep=24)

        # 2. 실시간 핫이슈 수집
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
                log_error_and_notify(f"Topic {topic} processing failed: {str(e)}")

    except Exception as e:
        log_error_and_notify(f"Main pipeline failed: {str(e)}")

def process_video(topic, project_id, bucket_name, elevenlabs_key, pexels_key, voice_id, youtube_creds, ai_manager):
    """단일 영상 처리 파이프라인"""
    logger.info(f"Processing topic: {topic}")
    
    # 1. AI로 콘텐츠 생성 (GPT-4o/Gemini 로테이션)
    current_ai = ai_manager.get_current_model()
    script = generate_script(topic, ai_manager)
    
    # 2. 음성 파일 생성
    audio_path = "/tmp/audio.mp3"
    generate_audio(script, audio_path, elevenlabs_key, voice_id)
    
    # 3. 배경 영상 다운로드
    video_url = download_pexels_video(pexels_key, topic)
    
    # 4. 영상 생성
    output_path = "/tmp/final.mp4"
    create_video(video_url, audio_path, output_path)
    
    # 5. Shorts 변환
    shorts_path = "/tmp/shorts.mp4"
    convert_to_shorts(output_path, shorts_path)
    
    # 6. YouTube 업로드
    uploader = YouTubeUploader(youtube_creds)
    uploader.upload_video(
        video_path=shorts_path,
        title=f"{topic} 최신 정보 🚀",
        description=f"{topic}에 관한 최신 업데이트입니다. #shorts #{topic.replace(' ', '')}",
        tags=["shorts", "자동생성", topic]
    )

if __name__ == "__main__":
    main()
