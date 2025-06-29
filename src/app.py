# src/app.py
import os
import logging
import json
import time
from datetime import datetime
from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor
import sys

# --- Flask 애플리케이션 객체 선언 (⭐Gunicorn 진입점⭐) ---
app = Flask(__name__)

# --- 로깅 설정 (app 객체 선언 후 바로) ---
try:
    import google.cloud.logging
    logging_client = google.cloud.logging.Client()
    logging_client.setup_logging()
    logging.info("✅ Google Cloud Logging이 설정되었습니다.")
except Exception as e:
    logging.warning(f"Google Cloud Logging 설정 실패 (일반 로깅 사용): {e}")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# --- 전역 변수 선언 ---
MODULE_IMPORT_FAILED = False
INITIALIZATION_ERROR = None
APP_INITIALIZED_SUCCESSFULLY = False

# --- 모듈 임포트 ---
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("✅ .env 파일 로드 시도 (로컬 개발용).")
except ImportError:
    logger.warning("python-dotenv 모듈 없음. 배포 환경에서는 무관.")

try:
    # Google Cloud
    from google.cloud import storage

    # Third-party APIs
    import requests
    from openai import OpenAI
    from google.generativeai import configure as configure_gemini
    from elevenlabs import set_api_key as set_elevenlabs_key
    from newsapi import NewsApiClient
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    import google.auth.transport.requests
    from pexels_api import API

    # 사용자 정의 모듈
    from video_script_generator import generate_script_from_news
    from audio_generator import generate_audio_from_text
    from video_generator import create_video_from_images_and_audio
    from youtube_uploader import upload_video_to_youtube
    from gcs_helper import upload_to_gcs, download_from_gcs, delete_from_gcs

except ImportError as e:
    logger.critical(f"❌ 필수 모듈 임포트 실패: {e}", exc_info=True)
    MODULE_IMPORT_FAILED = True
    INITIALIZATION_ERROR = f"필수 모듈 임포트 실패: {e}"

# --- ThreadPoolExecutor (비동기 처리) ---
executor = ThreadPoolExecutor(max_workers=os.cpu_count() * 2 if os.cpu_count() else 2)

# --- 전역 변수 초기화 ---
GCP_PROJECT_ID = None
GCP_BUCKET_NAME = None
YOUTUBE_CLIENT_ID = None
YOUTUBE_CLIENT_SECRET = None
YOUTUBE_REFRESH_TOKEN = None
ELEVENLABS_API_KEY = None
ELEVENLABS_VOICE_ID = None
OPENAI_API_KEYS = []
GEMINI_API_KEY = None
NEWSAPI_API_KEY = None
PEXELS_API_KEY = None
bucket = None
storage_client_instance = None

# --- 초기화 함수 ---
def initialize_app_logic():
    global GCP_PROJECT_ID, GCP_BUCKET_NAME, YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, \
           YOUTUBE_REFRESH_TOKEN, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, OPENAI_API_KEYS, \
           GEMINI_API_KEY, NEWSAPI_API_KEY, PEXELS_API_KEY, bucket, storage_client_instance, \
           APP_INITIALIZED_SUCCESSFULLY, INITIALIZATION_ERROR

    logger.info("🚀 애플리케이션 초기화 시작...")

    if MODULE_IMPORT_FAILED:
        logger.critical("모듈 임포트 실패로 초기화 중단.")
        APP_INITIALIZED_SUCCESSFULLY = False
        return

    required_env_vars = [
        'GCP_PROJECT_ID', 'GCP_BUCKET_NAME', 'YOUTUBE_CLIENT_ID', 'YOUTUBE_CLIENT_SECRET',
        'YOUTUBE_REFRESH_TOKEN', 'ELEVENLABS_API_KEY', 'ELEVENLABS_VOICE_ID',
        'OPENAI_API_KEYS', 'GEMINI_API_KEY', 'NEWSAPI_API_KEY', 'PEXELS_API_KEY'
    ]
    missing_vars = []

    for var_name in required_env_vars:
        value = os.getenv(var_name)
        if var_name == 'OPENAI_API_KEYS':
            if value:
                OPENAI_API_KEYS.clear()
                OPENAI_API_KEYS.extend([k.strip() for k in value.split(',') if k.strip()])
                if not OPENAI_API_KEYS:
                    missing_vars.append(var_name)
            else:
                missing_vars.append(var_name)
        elif not value:
            missing_vars.append(var_name)
        else:
            globals()[var_name] = value

    if missing_vars:
        INITIALIZATION_ERROR = f"필수 환경 변수 누락: {', '.join(missing_vars)}"
        logger.critical(INITIALIZATION_ERROR)
        APP_INITIALIZED_SUCCESSFULLY = False
        return

    try:
        storage_client_instance = storage.Client(project=GCP_PROJECT_ID)
        bucket = storage_client_instance.get_bucket(GCP_BUCKET_NAME)
        logger.info(f"✅ Cloud Storage 버킷 '{GCP_BUCKET_NAME}' 초기화 성공.")
    except Exception as e:
        INITIALIZATION_ERROR = f"Cloud Storage 초기화 실패: {e}"
        logger.critical(INITIALIZATION_ERROR, exc_info=True)
        APP_INITIALIZED_SUCCESSFULLY = False
        return

    try:
        set_elevenlabs_key(ELEVENLABS_API_KEY)
        configure_gemini(api_key=GEMINI_API_KEY)
        logger.info("✅ ElevenLabs 및 Gemini API 키 설정 완료.")
    except Exception as e:
        INITIALIZATION_ERROR = f"외부 API 키 설정 실패: {e}"
        logger.warning(INITIALIZATION_ERROR, exc_info=True)
        APP_INITIALIZED_SUCCESSFULLY = False
        return

    APP_INITIALIZED_SUCCESSFULLY = True
    logger.info("✅ 앱 초기화 성공.")

initialize_app_logic()

# --- healthz 엔드포인트 ---
@app.route('/healthz', methods=['GET'])
def healthz():
    if MODULE_IMPORT_FAILED or not APP_INITIALIZED_SUCCESSFULLY:
        msg = INITIALIZATION_ERROR or "Unknown initialization error"
        return f"Not Ready: {msg}", 500
    return "OK", 200

# --- 메인 엔드포인트 ---
@app.route("/", methods=["POST"])
def main_endpoint():
    if MODULE_IMPORT_FAILED or not APP_INITIALIZED_SUCCESSFULLY:
        msg = INITIALIZATION_ERROR or "Unknown initialization error"
        return jsonify({"status": "error", "message": msg}), 500

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "JSON payload가 제공되지 않았습니다"}), 400

    action = data.get('action', '')
    metadata = data.get('metadata', {})

    if action == 'create_and_upload_shorts':
        executor.submit(process_youtube_shorts_upload, metadata)
        return jsonify({"status": "processing", "message": "YouTube Shorts 업로드 프로세스 시작됨"}), 202
    else:
        return jsonify({"status": "error", "message": f"지원되지 않는 액션: {action}"}), 400

# --- YouTube Shorts 업로드 프로세스 ---
def process_youtube_shorts_upload(metadata):
    logger.info(f"▶️ YouTube Shorts 업로드 프로세스 시작: {metadata}")
    try:
        script_data = generate_script_from_news(NEWSAPI_API_KEY, OPENAI_API_KEYS, GEMINI_API_KEY, "최신 기술 뉴스")
        script = script_data.get('script', 'AI 자동 생성 스크립트입니다.')
        title = script_data.get('title', f"AI Shorts {datetime.now()}")

        audio_path = f"/tmp/audio_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp3"
        generate_audio_from_text(script, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, audio_path)

        pexels = API(PEXELS_API_KEY)
        pexels.search(script_data.get('search_keywords', 'technology'), page=1, results_per_page=1)
        photo = next(iter(pexels.get_entries()), None)
        if not photo:
            raise RuntimeError("Pexels에서 이미지를 찾을 수 없습니다.")
        img_url = photo.medium
        img_path = f"/tmp/image_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
        with open(img_path, 'wb') as f:
            f.write(requests.get(img_url).content)

        video_path = f"/tmp/video_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp4"
        create_video_from_images_and_audio([img_path], audio_path, video_path)

        gcs_path = f"shorts/{os.path.basename(video_path)}"
        upload_to_gcs(GCP_BUCKET_NAME, video_path, gcs_path, GCP_PROJECT_ID)

        downloaded_path = f"/tmp/downloaded_{os.path.basename(video_path)}"
        download_from_gcs(GCP_BUCKET_NAME, gcs_path, downloaded_path, GCP_PROJECT_ID)

        upload_video_to_youtube(
            YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN,
            downloaded_path, title, script
        )
        logger.info("✅ YouTube Shorts 업로드 완료.")
    except Exception as e:
        logger.error(f"❌ Shorts 업로드 실패: {e}", exc_info=True)

# --- 로컬 실행 진입점 ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
