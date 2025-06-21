# src/main.py
import functions_framework
import logging
import os
import json
import uuid
from datetime import datetime, timedelta

# 로깅 설정 (Cloud Functions에서 자동으로 Stackdriver Logging으로 통합됨)
# functions_framework는 이미 로깅을 설정하므로, 중복될 수 있지만 명시적으로 설정해도 무방합니다.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 프로젝트 내부 모듈 임포트
# Cloud Functions 환경에서는 상대 경로 임포트(`from .config import config`) 대신
# 절대 경로 임포트(`from src.config import config`)가 더 안전합니다.
# 이미 그렇게 되어 있으니 좋습니다.
from src.config import config
from src.trend_api import NewsAPI
from src.content_generator import ContentGenerator
from src.tts_generator import generate_audio
from src.video_creator import VideoCreator
from src.thumbnail_generator import ThumbnailGenerator
from src.youtube_uploader import YouTubeUploader
from src.comment_poster import CommentPoster
from src.cleanup_manager import cleanup_old_files
from src.openai_utils import api_key_manager # API 키 관리자 임포트

from google.cloud import storage
# Flask의 Request 객체를 타입 힌트로 사용 (functions_framework가 Flask Request를 래핑하여 제공)
from flask import Request

# Cloud Storage 클라이언트 초기화 (config에서 project_id, bucket_name 가져옴)
# 이 부분에서 config 초기화나 인증에 실패하면 컨테이너 헬스 체크 실패의 원인이 될 수 있습니다.
# 예를 들어, GCP_PROJECT_ID가 Secret Manager에서 아직 로드되지 않았거나,
# Cloud Function 서비스 계정에 Storage 접근 권한이 없을 경우.
try:
    logger.info("Initializing Cloud Storage client...")
    # config 객체가 이 시점에서 완전히 초기화되었는지 확인이 필요합니다.
    # config.py의 Config 클래스가 __init__에서 Secret Manager 클라이언트를 초기화하므로,
    # 만약 config.py에서 DefaultCredentialsError가 발생한다면, 이 라인 이전에 에러가 납니다.
    storage_client = storage.Client(project=config.project_id)
    bucket = storage_client.bucket(config.bucket_name)
    logger.info(f"Cloud Storage client initialized for bucket: {config.bucket_name}")
except Exception as e:
    logger.error(f"FATAL ERROR during Cloud Storage client initialization: {e}", exc_info=True)
    # Cloud Function 컨테이너가 시작될 수 있도록 여기서는 에러를 다시 발생시키지 않습니다.
    # 하지만 이 경우 함수가 제대로 작동하지 않을 것입니다.
    # 실제 배포 환경에서는 이 에러가 발생하면 컨테이너가 시작되지 않을 가능성이 높습니다.
    # Cloud Build logs 또는 Cloud Run logs에서 이 초기화 실패를 찾아야 합니다.
    raise # 초기화 실패는 치명적이므로 빌드/시작 단계에서 실패하도록 예외를 다시 발생시키는 것이 좋습니다.

def download_font_from_gcs(font_name: str = "Catfont.ttf"):
    """Cloud Storage에서 폰트 파일을 다운로드합니다."""
    font_dir = os.path.join("/tmp", "fonts")
    font_local_path = os.path.join(font_dir, font_name)
    
    if not os.path.exists(font_dir):
        os.makedirs(font_dir, exist_ok=True)
    
    try:
        blob = bucket.blob(f"fonts/{font_name}") # 버킷 내 폰트 경로
        if not blob.exists():
            # 폰트 파일이 GCS에 없으면 명확한 에러 메시지
            logger.error(f"Font file '{font_name}' not found in GCS bucket '{config.bucket_name}/fonts'. "
                         f"Please ensure it's uploaded to the 'fonts/' directory in your bucket.")
            raise FileNotFoundError(f"Font file '{font_name}' not found in GCS.")
            
        blob.download_to_filename(font_local_path)
        logger.info(f"Font '{font_name}' downloaded to {font_local_path}")
        return font_local_path
    except Exception as e:
        logger.error(f"Failed to download font '{font_name}' from GCS: {e}", exc_info=True)
        raise # 폰트 다운로드 실패는 치명적이므로 예외 발생

def upload_to_gcs(source_file_name: str, destination_blob_name: str):
    """로컬 파일을 Cloud Storage에 업로드합니다."""
    try:
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_name)
        logger.info(f"File {source_file_name} uploaded to gs://{config.bucket_name}/{destination_blob_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to upload {source_file_name} to GCS: {e}", exc_info=True)
        return False

@functions_framework.http
def youtube_automation_main(request: Request):
    """
    HTTP 요청을 받아 YouTube Shorts 자동화 프로세스를 시작하는 Cloud Function의 진입점.
    """
    logger.info("🚀 YouTube Shorts Automation Process Started!")
    
    request_json = request.get_json(silent=True)
    if request_json and 'daily_run' in request_json:
        logger.info("Triggered by daily scheduled run.")
    
    # 폰트 다운로드 (Cloud Functions는 ephemeral filesystem이므로 매 실행마다 /tmp에 다운로드)
    try:
        font_local_path = download_font_from_gcs()
    except Exception as e:
        logger.error(f"Critical error: Failed to download font. Aborting process. {e}")
        # 폰트 다운로드 실패 시 500 에러를 반환하여 함수 호출 실패를 알림
        return f"Failed to download font: {e}", 500

    # 하루에 5개 영상 제작 루프
    for i in range(config.daily_video_count):
        logger.info(f"🎬 Starting video creation process #{i+1}/{config.daily_video_count}")
        
        # 0. API 키 및 모델 선택 (로테이션 적용)
        ai_model_info = api_key_manager.get_ai_model_for_task()
        if not ai_model_info[0]: # 모델 또는 키를 가져오지 못하면 스킵
            logger.error("No AI model or key available for content generation. Skipping video creation.")
            continue # 다음 루프로 이동

        selected_ai_model, selected_api_key = ai_model_info
        
        try:
            # 1. 최신 트렌드 토픽 가져오기
            news_api = NewsAPI(api_key=config.news_api_key)
            trend_topics = news_api.get_trending_topics(count=1)
            if not trend_topics:
                logger.warning("No trending topics found. Skipping video creation.")
                continue
            topic = trend_topics[0]
            logger.info(f"🔍 Selected topic: {topic}")

            # 2. 스크립트 생성 (AI 로테이션 적용)
            content_generator = ContentGenerator(
                openai_api_key=selected_api_key if selected_ai_model == 'openai' else None,
                gemini_api_key=selected_api_key if selected_ai_model == 'gemini' else None,
                ai_model=selected_ai_model
            )
            script_text = content_generator.generate_script(topic)
            if not script_text:
                logger.error(f"Script generation failed for topic: {topic}. Skipping.")
                continue
            logger.info(f"📝 Script generated successfully for topic: {topic}")

            # 3. 음성 생성 (ElevenLabs)
            audio_filename = f"audio_{uuid.uuid4().hex}.mp3"
            audio_output_path = os.path.join("/tmp", audio_filename)
            
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
            video_output_path = os.path.join("/tmp", video_filename)
            
            video_creator = VideoCreator(font_path=font_local_path, pexels_api_key=config.pexels_api_key)
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
            thumbnail_output_path = os.path.join("/tmp", thumbnail_filename)

            thumbnail_generator = ThumbnailGenerator(font_path=font_local_path)
            thumbnail_success = thumbnail_generator.generate_thumbnail(
                text_content=topic,
                output_path=thumbnail_output_path
            )
            if not thumbnail_success:
                logger.warning(f"⚠️ Thumbnail generation failed for topic: {topic}. Proceeding without thumbnail.")
                thumbnail_output_path = None
            else:
                logger.info(f"🖼️ Thumbnail created at {thumbnail_output_path}")

            # 6. Cloud Storage에 영상 및 썸네일 업로드
            gcs_video_path = f"videos/{video_filename}"
            gcs_thumbnail_path = f"thumbnails/{thumbnail_filename}" if thumbnail_output_path else None

            video_uploaded = upload_to_gcs(video_output_path, gcs_video_path)
            if not video_uploaded:
                logger.error(f"❌ Failed to upload video to GCS: {video_output_path}. Skipping YouTube upload.")
                continue
            
            if gcs_thumbnail_path:
                thumbnail_uploaded = upload_to_gcs(thumbnail_output_path, gcs_thumbnail_path)
                if not thumbnail_uploaded:
                    logger.warning(f"⚠️ Failed to upload thumbnail to GCS: {thumbnail_output_path}. Proceeding without thumbnail.")
                    gcs_thumbnail_path = None
            
            logger.info(f"⬆️ Video and thumbnail uploaded to GCS.")

            # 7. YouTube에 업로드
            youtube_uploader = YouTubeUploader(
                client_id=config.youtube_client_id,
                client_secret=config.youtube_client_secret,
                refresh_token=config.youtube_refresh_token
            )
            
            video_title = f"🔥 최신 이슈: {topic} #shorts #뉴스 #이슈"
            video_description = f"오늘의 핫이슈, '{topic}'에 대한 짧은 요약 영상입니다.\n\n#shorts #news #trending #youtube"
            video_tags = ["shorts", "news", "trending", "issue", topic.replace(" ", "")]

            youtube_video_id = youtube_uploader.upload_video(
                video_file_path=video_output_path,
                title=video_title,
                description=video_description,
                tags=video_tags,
                privacy_status="public", # 테스트 시에는 "private"으로 설정 권장
                thumbnail_file_path=thumbnail_output_path
            )

            if youtube_video_id:
                logger.info(f"✅ Video successfully uploaded to YouTube! Video ID: {youtube_video_id}")
                # 8. 댓글 자동 작성 (업로드된 영상에)
                comment_poster = CommentPoster(
                    client_id=config.youtube_client_id,
                    client_secret=config.youtube_client_secret,
                    refresh_token=config.youtube_refresh_token
                )
                comment_text = "이 영상이 유익하셨다면 구독과 좋아요 부탁드립니다! 😊"
                comment_success = comment_poster.post_comment(youtube_video_id, comment_text)
                if comment_success:
                    logger.info(f"💬 Comment posted successfully on video {youtube_video_id}")
                else:
                    logger.warning(f"❌ Failed to post comment on video {youtube_video_id}")
            else:
                logger.error(f"❌ Failed to upload video to YouTube for topic: {topic}.")
        
        except Exception as e:
            logger.error(f"An error occurred during video creation process #{i+1}: {e}", exc_info=True)
        finally:
            # 임시 파일 정리 (Cloud Functions 환경에서는 /tmp 폴더가 재사용되므로 정리 필요)
            # 파일이 존재하고 있는지 확인 후 삭제
            for path in [audio_output_path, video_output_path, thumbnail_output_path]:
                # path가 None이거나 정의되지 않은 경우를 처리
                if path and isinstance(path, str) and os.path.exists(path):
                    try:
                        os.remove(path)
                        logger.info(f"Cleaned up {path}")
                    except OSError as os_err:
                        logger.warning(f"Could not remove temporary file {path}: {os_err}")

    # 모든 프로세스 완료 후 오래된 GCS 파일 정리 (매일 실행되므로 너무 자주 하지 않도록 주의)
    try:
        cleanup_old_files(bucket, retention_days=7)  
        logger.info("🗑️ Old GCS files cleaned up successfully.")
    except Exception as e:
        logger.error(f"Error during GCS cleanup: {e}", exc_info=True)

    logger.info("🎉 YouTube Shorts Automation Process Finished!")
    # Cloud Function은 HTTP 응답을 반환해야 합니다.
    return "YouTube Shorts Automation Process Finished Successfully!", 200

# Cloud Function 배포 시에는 Flask 앱 인스턴스 없이도 request 객체를 직접 주입합니다.
# 따라서 Flask app = Flask(__name__) 형태의 코드는 Cloud Functions 런타임에서는 필요 없습니다.
