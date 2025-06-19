# src/batch_processor.py
import os
import logging
import json
import time
from datetime import datetime, timedelta

# 로컬 테스트 환경을 위한 환경 변수 로드 (배포 시에는 GCP 환경 변수 사용)
from dotenv import load_dotenv
load_dotenv()

# 모듈 임포트
from src.config import get_secret, setup_logging
from src.ai_manager import AIManager
from src.content_curator import ContentCurator
from src.content_generator import generate_content_with_ai
from src.bg_downloader import download_pexels_videos
from src.tts_generator import generate_audio
from src.video_creator import create_video_from_frames
from src.thumbnail_generator import generate_thumbnail
from src.youtube_uploader import upload_video_to_youtube
from src.shorts_converter import convert_to_shorts
from src.cleanup_manager import cleanup_old_files
from src.error_handler import log_error_and_notify # 에러 처리 추가
from src.utils import generate_unique_id, upload_to_gcs, download_from_gcs, check_gcs_file_exists, delete_gcs_file

# 로깅 설정
setup_logging()
logger = logging.getLogger(__name__)

# 전역 설정
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
GCP_BUCKET_NAME = os.environ.get("GCP_BUCKET_NAME")
ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "uyVNoMrnUku1dZyVEXwD") # 안나 킴

# AI Manager 초기화 (API 키는 get_secret을 통해 Secret Manager에서 동적으로 로드)
ai_manager = AIManager()

def main_automation_pipeline():
    """
    YouTube Shorts 자동화 파이프라인의 메인 실행 함수입니다.
    콘텐츠 생성부터 업로드까지의 전 과정을 담당합니다.
    """
    logger.info("Starting YouTube Automation Pipeline...")
    start_time = time.time()
    video_count = 0

    try:
        # 1. API 키 로드 (Secret Manager에서 동적으로 로드)
        logger.info("Loading API keys from Secret Manager...")
        elevenlabs_api_key = get_secret("ELEVENLABS_API_KEY")
        pexels_api_key = get_secret("PEXELS_API_KEY")
        news_api_key = get_secret("NEWS_API_KEY")
        youtube_oauth_credentials_json = get_secret("YOUTUBE_OAUTH_CREDENTIALS")
        
        # OpenAI 키는 AIManager 내부에서 관리하므로 별도로 로드할 필요 없음

        if not all([elevenlabs_api_key, pexels_api_key, news_api_key, youtube_oauth_credentials_json]):
            raise ValueError("One or more essential API keys or credentials are missing from Secret Manager.")

        # 2. 기존 파일 정리 (Cloud Storage 버킷) - 무료 할당량 관리
        logger.info(f"Cleaning up old files in GCS bucket: {GCP_BUCKET_NAME}...")
        cleanup_old_files(GCP_BUCKET_NAME, hours_to_keep=24) # 24시간 이전 파일 삭제

        # 3. 콘텐츠 주제 생성 (뉴스 API 활용)
        logger.info("Generating content topics based on hot issues...")
        curator = ContentCurator(news_api_key)
        hot_topics = curator.get_hot_topics(query="technology OR science OR daily news", num_topics=2) # 하루 2개 영상 예시
        if not hot_topics:
            logger.warning("No hot topics found. Using a default topic.")
            hot_topics = ["The Future of AI", "Space Exploration Latest Discoveries"]

        # 4. 여러 영상 제작 및 업로드 반복
        for i, topic in enumerate(hot_topics):
            unique_id = generate_unique_id()
            base_filename = f"youtube_shorts_{unique_id}"
            
            logger.info(f"Processing video {i+1}/{len(hot_topics)} for topic: '{topic}'")

            try:
                # 4.1. AI를 활용한 콘텐츠 생성 (GPT-4o, Gemini 로테이션)
                logger.info(f"Generating content for '{topic}' using AI...")
                current_ai_model = ai_manager.get_current_model()
                logger.info(f"Using AI model: {current_ai_model}")
                generated_content = generate_content_with_ai(topic, current_ai_model)
                if not generated_content:
                    log_error_and_notify(f"Failed to generate content for topic: {topic}")
                    continue
                
                script_text = generated_content.get("script", "Generated script is empty.")
                title = generated_content.get("title", f"Amazing Shorts on {topic}")
                tags = generated_content.get("tags", f"shorts, {topic.replace(' ', ',')}, youtube").split(',')
                description = generated_content.get("description", f"This short video explores {topic}.")

                # 4.2. 배경 영상 다운로드 (Pexels API)
                logger.info(f"Downloading background video for '{topic}'...")
                video_url = download_pexels_videos(pexels_api_key, query=topic, max_videos=1)
                if not video_url:
                    log_error_and_notify(f"Failed to download background video for topic: {topic}")
                    continue
                
                # 배경 영상 GCS에 업로드 (로컬 용량 확보)
                video_local_path = f"/tmp/{base_filename}_bg.mp4"
                # TODO: download_pexels_videos 함수가 url을 반환하고, 이 url을 직접 다운로드하는 로직 필요
                # 현재 로직은 download_pexels_videos가 내부적으로 저장한다고 가정.
                # 편의상 직접 wget으로 다운로드하는 예시 (실제 구현 시 bg_downloader.py에 로직 추가)
                try:
                    import subprocess
                    subprocess.run(["wget", "-O", video_local_path, video_url], check=True)
                    logger.info(f"Background video downloaded to {video_local_path}")
                except Exception as e:
                    log_error_and_notify(f"Error downloading background video from URL {video_url}: {e}")
                    continue
                
                gcs_video_path = f"raw_videos/{base_filename}_bg.mp4"
                upload_to_gcs(GCP_BUCKET_NAME, video_local_path, gcs_video_path)
                os.remove(video_local_path) # 로컬 파일 삭제

                # 4.3. 음성 생성 (ElevenLabs)
                logger.info("Generating audio for the script...")
                audio_local_path = f"/tmp/{base_filename}_audio.mp3"
                if not generate_audio(script_text, audio_local_path, elevenlabs_api_key, ELEVENLABS_VOICE_ID):
                    log_error_and_notify(f"Failed to generate audio for topic: {topic}")
                    continue
                
                # 음성 파일 GCS에 업로드 (로컬 용량 확보)
                gcs_audio_path = f"audios/{base_filename}_audio.mp3"
                upload_to_gcs(GCP_BUCKET_NAME, audio_local_path, gcs_audio_path)
                os.remove(audio_local_path) # 로컬 파일 삭제

                # 4.4. 영상 제작 (영상, 음성 결합)
                logger.info("Creating the final video...")
                final_video_local_path = f"/tmp/{base_filename}_final.mp4"
                if not create_video_from_frames(gcs_video_path, gcs_audio_path, final_video_local_path, GCP_BUCKET_NAME):
                    log_error_and_notify(f"Failed to create video for topic: {topic}")
                    continue

                # 4.5. Shorts 변환 (60초 이하, 최적화)
                logger.info("Converting video to Shorts format...")
                shorts_video_local_path = f"/tmp/{base_filename}_shorts.mp4"
                if not convert_to_shorts(final_video_local_path, shorts_video_local_path):
                    log_error_and_notify(f"Failed to convert video to Shorts for topic: {topic}")
                    continue
                os.remove(final_video_local_path) # 중간 파일 삭제

                # 4.6. 썸네일 자동 생성
                logger.info("Generating thumbnail...")
                thumbnail_local_path = f"/tmp/{base_filename}_thumbnail.jpg"
                if not generate_thumbnail(shorts_video_local_path, thumbnail_local_path):
                    log_error_and_notify(f"Failed to generate thumbnail for topic: {topic}")
                    continue
                
                # Shorts 영상 및 썸네일 GCS에 업로드
                gcs_shorts_path = f"shorts/{base_filename}_shorts.mp4"
                gcs_thumbnail_path = f"thumbnails/{base_filename}_thumbnail.jpg"
                upload_to_gcs(GCP_BUCKET_NAME, shorts_video_local_path, gcs_shorts_path)
                upload_to_gcs(GCP_BUCKET_NAME, thumbnail_local_path, gcs_thumbnail_path)
                
                os.remove(shorts_video_local_path)
                os.remove(thumbnail_local_path)
                
                # 4.7. YouTube 업로드
                logger.info("Uploading video to YouTube...")
                # youtube_oauth_credentials_json은 JSON 문자열이므로 파싱해야 합니다.
                youtube_credentials = json.loads(youtube_oauth_credentials_json)
                
                video_url = upload_video_to_youtube(
                    shorts_video_local_path, # 실제 업로드 시에는 GCS URL 대신 다운로드 받아 업로드
                    title,
                    description,
                    tags,
                    GCP_PROJECT_ID, # 프로젝트 ID 전달
                    thumbnail_path=thumbnail_local_path, # 실제 업로드 시에는 GCS URL 대신 다운로드 받아 업로드
                    oauth_credentials=youtube_credentials
                )
                if video_url:
                    logger.info(f"Video uploaded successfully! URL: {video_url}")
                    video_count += 1
                else:
                    log_error_and_notify(f"Failed to upload video for topic: {topic}")

                # 4.8. 댓글 자동 작성 (선택 사항) - YouTube API 쿼터 고려하여 신중하게 사용
                # comment_poster.post_comment(video_id, "Interesting video!", youtube_credentials)

                # API 쿼터 사용량 모니터링 (가상)
                logger.info(f"API usage for this video: OpenAI={ai_manager.get_api_usage('openai')}, Gemini={ai_manager.get_api_usage('gemini')}, ElevenLabs=..., Pexels=..., YouTube=...")

            except Exception as e:
                log_error_and_notify(f"Error processing video for topic '{topic}': {e}", exc_info=True)
                continue # 다음 영상 처리를 위해 계속 진행

    except Exception as e:
        log_error_and_notify(f"Critical error in main automation pipeline: {e}", exc_info=True)

    finally:
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"YouTube Automation Pipeline completed. Total videos uploaded: {video_count}. Total duration: {duration:.2f} seconds.")
        # 작업 완료 후에도 cleanup_manager는 주기적으로 실행되므로 여기서 추가 정리 필요 없음

if __name__ == "__main__":
    main_automation_pipeline()
