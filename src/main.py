# src/main.py
import logging
import os
import json
import uuid
from datetime import datetime, timedelta

# 로깅 설정 (Cloud Functions에서 자동으로 Stackdriver Logging으로 통합됨)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 프로젝트 내부 모듈 임포트
from src.config import config
from src.trend_api import NewsAPI
from src.content_generator import ContentGenerator
from src.tts_generator import generate_audio
from src.video_creator import VideoCreator
from src.thumbnail_generator import ThumbnailGenerator
from src.youtube_uploader import YouTubeUploader
from src.comment_poster import CommentPoster
from src.cleanup_manager import cleanup_old_files
from google.cloud import storage

# Cloud Storage 클라이언트 초기화
storage_client = storage.Client(project=config.project_id)
bucket = storage_client.bucket(config.bucket_name)

def download_font_from_gcs(font_name: str = "Catfont.ttf"):
    """Cloud Storage에서 폰트 파일을 다운로드합니다."""
    font_local_path = os.path.join("fonts", font_name)
    if not os.path.exists(os.path.dirname(font_local_path)):
        os.makedirs(os.path.dirname(font_local_path), exist_ok=True)
    
    try:
        blob = bucket.blob(f"fonts/{font_name}") # 버킷 내 폰트 경로
        blob.download_to_filename(font_local_path)
        logger.info(f"Font '{font_name}' downloaded to {font_local_path}")
        return font_local_path
    except Exception as e:
        logger.error(f"Failed to download font '{font_name}' from GCS: {e}")
        # 로컬에 폰트가 없으면 에러 발생하므로, 대체 폰트 경로 등을 고려하거나 에러 처리 필요
        raise

def upload_to_gcs(source_file_name: str, destination_blob_name: str):
    """로컬 파일을 Cloud Storage에 업로드합니다."""
    try:
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_name)
        logger.info(f"File {source_file_name} uploaded to gs://{config.bucket_name}/{destination_blob_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to upload {source_file_name} to GCS: {e}")
        return False

def youtube_automation_main(request):
    """
    HTTP 요청을 받아 YouTube Shorts 자동화 프로세스를 시작하는 Cloud Function의 진입점.
    """
    logger.info("🚀 YouTube Shorts Automation Process Started!")
    
    # 요청 본문 파싱 (스케줄링된 작업의 경우 비어있을 수 있음)
    request_json = request.get_json(silent=True)
    if request_json and 'daily_run' in request_json:
        logger.info("Triggered by daily scheduled run.")
    
    # 폰트 다운로드 (Cloud Functions는 ephemeral filesystem이므로 매 실행마다 다운로드)
    try:
        font_local_path = download_font_from_gcs()
    except Exception as e:
        logger.error(f"Critical error: Failed to download font. Aborting process. {e}")
        return "Failed to download font", 500

    # 하루에 5개 영상 제작 루프
    for i in range(config.daily_video_count):
        logger.info(f"🎬 Starting video creation process #{i+1}/{config.daily_video_count}")
        try:
            # 1. 최신 트렌드 토픽 가져오기
            news_api = NewsAPI(api_key=config.news_api_key)
            trend_topics = news_api.get_trending_topics(count=1) # 한 번에 한 개씩 가져옴
            if not trend_topics:
                logger.warning("No trending topics found. Skipping video creation.")
                continue
            topic = trend_topics[0]
            logger.info(f"🔍 Selected topic: {topic}")

            # 2. 스크립트 생성 (AI 로테이션 적용)
            content_generator = ContentGenerator()
            script_text = content_generator.generate_script(topic)
            if not script_text:
                logger.error(f"Script generation failed for topic: {topic}. Skipping.")
                continue
            logger.info(f"📝 Script generated successfully for topic: {topic}")

            # 3. 음성 생성 (ElevenLabs)
            audio_filename = f"audio_{uuid.uuid4().hex}.mp3"
            audio_output_path = os.path.join("/tmp", audio_filename) # Cloud Functions는 /tmp에만 쓰기 가능
            
            audio_success = generate_audio(
                text=script_text, 
                output_path=audio_output_path, 
                api_key=config.elevenlabs_api_key, 
                voice_id=config.elevenlabs_voice_id
            )
            if not audio_success:
                logger.error(f"❌ ElevenLabs audio generation failed for topic: {topic}. Skipping.")
                continue
            logger.info(f"🎙️ Audio generated at {audio_output_path}")

            # 4. 영상 생성
            video_filename = f"shorts_{uuid.uuid4().hex}.mp4"
            video_output_path = os.path.join("/tmp", video_filename) # Cloud Functions는 /tmp에만 쓰기 가능
            
            video_creator = VideoCreator(font_path=font_local_path)
            video_success = video_creator.create_video(
                audio_path=audio_output_path,
                text_content=script_text,
                output_path=video_output_path
            )
            if not video_success:
                logger.error(f"❌ Video creation failed for topic: {topic}. Skipping.")
                continue
            logger.info(f"🎬 Video created at {video_output_path}")

            # 5. 썸네일 생성
            thumbnail_filename = f"thumbnail_{uuid.uuid4().hex}.jpg"
            thumbnail_output_path = os.path.join("/tmp", thumbnail_filename) # Cloud Functions는 /tmp에만 쓰기 가능

            thumbnail_generator = ThumbnailGenerator(font_path=font_local_path)
            thumbnail_success = thumbnail_generator.generate_thumbnail(
                text_content=topic, # 주제로 썸네일 생성
                output_path=thumbnail_output_path
            )
            if not thumbnail_success:
                logger.warning(f"⚠️ Thumbnail generation failed for topic: {topic}. Proceeding without custom thumbnail.")
                thumbnail_output_path = None # 썸네일 생성 실패 시 None으로 설정

            # 6. Cloud Storage에 영상 및 썸네일 업로드
            gcs_video_path = f"shorts/{datetime.now().strftime('%Y/%m/%d')}/{video_filename}"
            upload_success = upload_to_gcs(video_output_path, gcs_video_path)
            if not upload_success:
                logger.error(f"❌ Failed to upload video to GCS for topic: {topic}. Skipping YouTube upload.")
                continue
            
            gcs_thumbnail_path = None
            if thumbnail_output_path:
                gcs_thumbnail_path = f"thumbnails/{datetime.now().strftime('%Y/%m/%d')}/{thumbnail_filename}"
                thumbnail_upload_success = upload_to_gcs(thumbnail_output_path, gcs_thumbnail_path)
                if not thumbnail_upload_success:
                    logger.warning(f"⚠️ Failed to upload thumbnail to GCS. YouTube upload will proceed without custom thumbnail.")
                    gcs_thumbnail_path = None

            # 7. YouTube에 영상 업로드
            youtube_uploader = YouTubeUploader(
                client_id=config.youtube_client_id,
                client_secret=config.youtube_client_secret,
                refresh_token=config.youtube_refresh_token
            )
            youtube_video_id = youtube_uploader.upload_video(
                video_file_path=video_output_path, # 로컬 경로 사용, Uploader 내부에서 Stream으로 처리
                title=f"[쇼츠] {topic} - 오늘 뭐볼까?",
                description=f"오늘의 핫이슈 {topic}에 대한 짧은 영상입니다. #Shorts #핫이슈 #{topic.replace(' ', '')}",
                tags=[topic, "쇼츠", "핫이슈", "AI생성"],
                privacy_status="public", # 테스트 시에는 "private"으로 설정 권장
                thumbnail_file_path=thumbnail_output_path
            )
            if not youtube_video_id:
                logger.error(f"❌ YouTube upload failed for topic: {topic}.")
                continue
            logger.info(f"🎥 Video uploaded to YouTube! Video ID: {youtube_video_id}")

            # 8. YouTube 댓글 자동 작성
            comment_poster = CommentPoster(
                client_id=config.youtube_client_id,
                client_secret=config.youtube_client_secret,
                refresh_token=config.youtube_refresh_token
            )
            comment_success = comment_poster.post_comment(
                video_id=youtube_video_id,
                comment_text=f"이 영상이 좋으셨다면 구독과 좋아요 부탁드립니다! #{topic.replace(' ', '')} #자동생성"
            )
            if not comment_success:
                logger.warning(f"⚠️ Failed to post comment for video ID: {youtube_video_id}")
            else:
                logger.info(f"💬 Comment posted for video ID: {youtube_video_id}")

            # 9. 임시 파일 정리 (Cloud Functions는 함수 실행 후 자동 삭제되지만, 명시적 정리)
            os.remove(audio_output_path)
            os.remove(video_output_path)
            if thumbnail_output_path and os.path.exists(thumbnail_output_path):
                os.remove(thumbnail_output_path)
            logger.info(f"🗑️ Cleaned up temporary files for video #{i+1}.")

        except Exception as e:
            logger.error(f"❌ Error during video creation process #{i+1}: {e}", exc_info=True)
            # 개별 영상 생성 실패 시에도 다음 영상 생성을 시도하도록 continue

    logger.info("✅ Overall YouTube Shorts Automation Process Completed.")

    # 오래된 Cloud Storage 파일 정리 (매일 한 번만 실행되도록 스케줄링)
    # Cloud Functions는 매번 실행되므로, 이 클린업 로직은 스케줄러에서 적절히 호출되도록 해야 함
    # 현재는 매번 실행될 때마다 지난 7일치 데이터를 정리하도록 설정
    cleanup_date = datetime.now() - timedelta(days=7)
    cleanup_manager = cleanup_old_files(bucket=bucket, days_old=7)
    logger.info(f"🗑️ Running Cloud Storage cleanup for files older than {cleanup_date.strftime('%Y-%m-%d')}")
    
    return "YouTube Shorts automation process finished.", 200
