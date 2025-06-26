# src/main.py

import os
import logging
import functions_framework
from flask import jsonify # Flask에서 jsonify를 명시적으로 임포트
from google.cloud import storage # Cloud Storage 클라이언트 임포트
from google.cloud import secretmanager # Secret Manager 클라이언트 임포트

# ⭐ 수정된 부분: tts_generator 임포트 시 상대 경로 '.' 추가
from .tts_generator import generate_tts_audio
from .video_creator import create_short_video
from .youtube_uploader import YoutubeUploader
from .api_clients import (
    fetch_news_articles,
    generate_openai_text,
    generate_pexels_video_url,
    generate_gemini_text
)

# 로거 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 환경 변수 및 Secret Manager에서 값 불러오기
# Cloud Functions 환경 변수 (Cloud Build 시점에 설정)
GCP_PROJECT_ID = os.environ.get('GCP_PROJECT_ID')
GCP_BUCKET_NAME = os.environ.get('GCP_BUCKET_NAME')

# Secret Manager에서 Secrets 불러오기
def get_secret(secret_name):
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{GCP_PROJECT_ID}/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.error(f"Failed to access secret {secret_name}: {e}", exc_info=True)
        raise

# 전역 변수로 Secret 값들을 캐시 (함수 호출마다 Secret Manager 접근 방지)
# 함수가 처음 로드될 때 한 번만 실행됨
try:
    OPENAI_API_KEYS = get_secret("OPENAI_API_KEYS")
    PEXELS_API_KEY = get_secret("PEXELS_API_KEY")
    YOUTUBE_CLIENT_ID = get_secret("YOUTUBE_CLIENT_ID")
    YOUTUBE_CLIENT_SECRET = get_secret("YOUTUBE_CLIENT_SECRET")
    YOUTUBE_REFRESH_TOKEN = get_secret("YOUTUBE_REFRESH_TOKEN")
    ELEVENLABS_API_KEY = get_secret("ELEVENLABS_API_KEY")
    ELEVENLABS_VOICE_ID = get_secret("ELEVENLABS_VOICE_ID")
    GEMINI_API_KEY = get_secret("GEMINI_API_KEY")
    NEWSAPI_API_KEY = get_secret("NEWSAPI_API_KEY") # 추가된 Secret
    logger.info("Secrets loaded successfully.")
except Exception as e:
    logger.error(f"Error loading secrets: {e}", exc_info=True)
    # Secrets 로드 실패 시 함수가 제대로 동작하지 않으므로 예외 발생
    raise RuntimeError("Failed to load required secrets.")

# MoviePy가 FFmpeg 바이너리를 찾도록 환경 변수 설정
# Dockerfile에서 ffmpeg을 /usr/bin/ffmpeg에 설치하므로, 해당 경로를 명시
os.environ["FFMPEG_BINARY"] = "/usr/bin/ffmpeg"
os.environ["FFPROBE_BINARY"] = "/usr/bin/ffprobe"
logger.info(f"FFMPEG_BINARY set to: {os.environ.get('FFMPEG_BINARY')}")
logger.info(f"FFPROBE_BINARY set to: {os.environ.get('FFPROBE_BINARY')}")


# Cloud Storage 클라이언트 초기화
storage_client = storage.Client(project=GCP_PROJECT_ID)
bucket = storage_client.get_bucket(GCP_BUCKET_NAME)

def upload_to_gcs(source_file_name, destination_blob_name):
    """GCS에 파일을 업로드합니다."""
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    logger.info(f"File {source_file_name} uploaded to {destination_blob_name}.")
    return f"gs://{GCP_BUCKET_NAME}/{destination_blob_name}"

def delete_local_file(file_path):
    """로컬 파일을 삭제합니다."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Local file deleted: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to delete local file {file_path}: {e}")

@functions_framework.http
def trigger_youtube_upload(request):
    """
    HTTP 요청을 받아 YouTube 쇼츠 비디오 생성 및 업로드 프로세스를 시작합니다.
    """
    logger.info("Cloud Function 'trigger_youtube_upload' 호출됨.")
    
    # 요청 본문 파싱 (선택 사항)
    request_json = request.get_json(silent=True)
    if request_json and 'daily_run' in request_json:
        is_daily_run = request_json['daily_run']
    else:
        is_daily_run = False # 기본값

    try:
        # 1. 뉴스 기사 요약 및 스크립트 생성 (GPT-4o 또는 Gemini)
        logger.info("뉴스 기사 요약 및 스크립트 생성 시작...")
        news_articles = fetch_news_articles(NEWSAPI_API_KEY)
        
        if not news_articles:
            logger.warning("뉴스 기사를 찾을 수 없습니다. 프로세스를 종료합니다.")
            return jsonify({"status": "warning", "message": "No news articles found."}), 200

        # OpenAI 사용 (기본)
        script_text_openai = generate_openai_text(OPENAI_API_KEYS, news_articles)
        logger.info(f"OpenAI를 사용한 스크립트: {script_text_openai[:100]}...")

        # Gemini 사용 (대체 또는 추가)
        # script_text_gemini = generate_gemini_text(GEMINI_API_KEY, news_articles)
        # logger.info(f"Gemini를 사용한 스크립트: {script_text_gemini[:100]}...")
        
        # 실제 사용할 스크립트 선택 (여기서는 OpenAI 사용)
        final_script_text = script_text_openai

        if not final_script_text:
            raise RuntimeError("스크립트 생성을 실패했습니다.")
        logger.info("스크립트 생성 완료.")

        # 2. TTS 오디오 생성 (ElevenLabs)
        audio_output_path = "/tmp/generated_audio.mp3"
        logger.info(f"음성 오디오 생성 시작... (Voice ID: {ELEVENLABS_VOICE_ID})")
        generate_tts_audio(
            api_key=ELEVENLABS_API_KEY,
            content=final_script_text,
            voice_id=ELEVENLABS_VOICE_ID,
            file_path=audio_output_path
        )
        logger.info("음성 오디오 생성 완료.")

        # 3. 배경 영상 검색 및 다운로드 (Pexels)
        video_query = "nature relaxing" # 또는 스크립트 내용 기반으로 동적 생성
        background_video_path = "/tmp/background_video.mp4"
        logger.info(f"배경 영상 검색 및 다운로드 시작... (쿼리: {video_query})")
        
        pexels_video_url = generate_pexels_video_url(PEXELS_API_KEY, video_query)
        if not pexels_video_url:
            raise RuntimeError("Pexels에서 적절한 배경 영상을 찾을 수 없습니다.")
        
        # requests로 영상 다운로드
        import requests
        response = requests.get(pexels_video_url, stream=True)
        response.raise_for_status()
        with open(background_video_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info(f"배경 영상 다운로드 완료: {background_video_path}")


        # 4. 쇼츠 비디오 생성
        output_video_path = "/tmp/final_short.mp4"
        logger.info("최종 쇼츠 비디오 생성 시작...")
        create_short_video(background_video_path, audio_output_path, output_video_path)
        logger.info("최종 쇼츠 비디오 생성 완료.")

        # 5. 생성된 비디오를 GCS에 업로드
        gcs_video_name = f"youtube_shorts/{os.path.basename(output_video_path)}"
        gcs_video_url = upload_to_gcs(output_video_path, gcs_video_name)
        logger.info(f"비디오가 GCS에 업로드되었습니다: {gcs_video_url}")

        # 6. YouTube에 비디오 업로드
        logger.info("YouTube 업로드 시작...")
        uploader = YoutubeUploader(
            client_id=YOUTUBE_CLIENT_ID,
            client_secret=YOUTUBE_CLIENT_SECRET,
            refresh_token=YOUTUBE_REFRESH_TOKEN
        )
        video_title = "오늘의 쇼츠 뉴스 - AI 생성 비디오" # 또는 스크립트 기반 동적 생성
        video_description = final_script_text[:400] + "..." # 스크립트 앞부분을 설명으로
        video_tags = ["뉴스", "AI", "쇼츠", "자동화"]

        youtube_video_id = uploader.upload_video(
            file_path=output_video_path,
            title=video_title,
            description=video_description,
            tags=video_tags,
            category="25",  # News & Politics 카테고리 ID
            privacy_status="public" # "private", "unlisted", "public"
        )
        logger.info(f"YouTube 업로드 완료. 비디오 ID: {youtube_video_id}")

        return jsonify({
            "status": "success",
            "message": "YouTube 쇼츠 비디오가 성공적으로 생성 및 업로드되었습니다.",
            "youtube_video_id": youtube_video_id,
            "gcs_video_url": gcs_video_url
        }), 200

    except Exception as e:
        logger.error(f"🔥 프로세스 중 치명적인 오류 발생: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        # 임시 파일 정리
        delete_local_file(audio_output_path)
        delete_local_file(background_video_path)
        delete_local_file(output_video_path)
