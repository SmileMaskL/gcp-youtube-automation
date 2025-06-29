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
    # dotenv는 로컬 개발용입니다. Cloud Run에서는 사용되지 않습니다.
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("✅ .env 파일 로드 시도 (로컬 개발용).")
except ImportError:
    logger.warning("python-dotenv 모듈 없음. 배포 환경에서는 무관.")

try:
    # Google Cloud
    from google.cloud import storage

    # Third-party APIs (GPT-4o, Gemini 포함)
    import requests
    from openai import OpenAI # GPT-4o 사용
    from google.generativeai import configure as configure_gemini # Google Gemini 사용
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
OPENAI_API_KEYS = [] # 콤마(,)로 구분된 여러 키를 저장할 리스트
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
                # ⭐ 중요: OPENAI_API_KEYS 환경 변수가 콤마(,)로 구분되어야 합니다.
                # GitHub Actions의 deploy-and-run.yml에서 이 포맷으로 넘겨줘야 합니다.
                OPENAI_API_KEYS.clear()
                OPENAI_API_KEYS.extend([k.strip() for k in value.split(',') if k.strip()])
                if not OPENAI_API_KEYS:
                    missing_vars.append(var_name)
            else:
                missing_vars.append(var_name)
        elif not value:
            missing_vars.append(var_name)
        else:
            # global 변수에 환경 변수 값 할당
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
        configure_gemini(api_key=GEMINI_API_KEY) # Google Gemini API 설정
        logger.info("✅ ElevenLabs 및 Gemini API 키 설정 완료.")
    except Exception as e:
        INITIALIZATION_ERROR = f"외부 API 키 설정 실패: {e}"
        logger.warning(INITIALIZATION_ERROR, exc_info=True)
        APP_INITIALIZED_SUCCESSFULLY = False
        return

    APP_INITIALIZED_SUCCESSFULLY = True
    logger.info("✅ 앱 초기화 성공.")

# 앱 시작 시 초기화 함수 호출
initialize_app_logic()

# --- healthz 엔드포인트 ---
@app.route('/healthz', methods=['GET'])
def healthz():
    # 모듈 임포트 실패 또는 앱 초기화 실패 시 500 에러 반환
    if MODULE_IMPORT_FAILED or not APP_INITIALIZED_SUCCESSFULLY:
        msg = INITIALIZATION_ERROR or "Unknown initialization error"
        logger.error(f"❌ Health Check Failed: {msg}") # healthz에서도 에러 로깅 추가
        return f"Not Ready: {msg}", 500
    return "OK", 200

# --- 메인 엔드포인트 ---
@app.route("/", methods=["POST"])
def main_endpoint():
    # 모듈 임포트 실패 또는 앱 초기화 실패 시 500 에러 반환
    if MODULE_IMPORT_FAILED or not APP_INITIALIZED_SUCCESSFULLY:
        msg = INITIALIZATION_ERROR or "Unknown initialization error"
        logger.error(f"❌ Main Endpoint Call Failed due to initialization error: {msg}") # 에러 로깅 추가
        return jsonify({"status": "error", "message": msg}), 500

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "JSON payload가 제공되지 않았습니다"}), 400

    action = data.get('action', '')
    metadata = data.get('metadata', {})

    if action == 'create_and_upload_shorts':
        # 비동기 처리를 위해 ThreadPoolExecutor 사용
        executor.submit(process_youtube_shorts_upload, metadata)
        return jsonify({"status": "processing", "message": "YouTube Shorts 업로드 프로세스 시작됨"}), 202
    else:
        return jsonify({"status": "error", "message": f"지원되지 않는 액션: {action}"}), 400

# --- YouTube Shorts 업로드 프로세스 ---
def process_youtube_shorts_upload(metadata):
    logger.info(f"▶️ YouTube Shorts 업로드 프로세스 시작: {metadata}")
    audio_path = None
    img_path = None
    video_path = None
    downloaded_path = None
    
    try:
        # 뉴스 주제를 동적으로 변경하려면 metadata에서 받아올 수 있습니다.
        news_topic = metadata.get('news_topic', '최신 기술 뉴스') # 기본값 설정
        script_data = generate_script_from_news(NEWSAPI_API_KEY, OPENAI_API_KEYS, GEMINI_API_KEY, news_topic)
        script = script_data.get('script', 'AI 자동 생성 스크립트입니다.')
        title = script_data.get('title', f"AI Shorts {datetime.now().strftime('%Y%m%d%H%M%S')}")

        audio_path = f"/tmp/audio_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp3"
        generate_audio_from_text(script, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, audio_path)

        pexels = API(PEXELS_API_KEY)
        # 검색 키워드를 스크립트 데이터에서 가져오고, 없으면 'technology' 사용
        search_keywords = script_data.get('search_keywords', 'technology, innovation') 
        pexels.search(search_keywords, page=1, results_per_page=1)
        photo = next(iter(pexels.get_entries()), None)
        
        if photo:
            img_url = photo.medium
            img_path = f"/tmp/image_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
            with open(img_path, 'wb') as f:
                f.write(requests.get(img_url).content)
            logger.info(f"✅ Pexels 이미지 다운로드 성공: {img_url}")
        else:
            logger.warning("⚠️ Pexels에서 이미지를 찾을 수 없습니다. 기본 이미지를 사용합니다.")
            # ⭐ 중요: 이 'default_image.jpg' 파일은 Dockerfile을 통해 /app/default_image.jpg 경로에 있어야 합니다.
            # Dockerfile에 `COPY default_image.jpg /app/default_image.jpg` 추가가 필요합니다.
            img_path = "/app/default_image.jpg" 
            if not os.path.exists(img_path):
                # 만약 기본 이미지도 없다면, 에러 로깅 후 종료 (최후의 수단)
                raise FileNotFoundError(f"기본 이미지 파일이 '{img_path}' 경로에 없습니다. Dockerfile 확인 필요.")


        video_path = f"/tmp/video_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp4"
        create_video_from_images_and_audio([img_path], audio_path, video_path)

        gcs_path = f"shorts/{os.path.basename(video_path)}"
        upload_to_gcs(GCP_BUCKET_NAME, video_path, gcs_path, GCP_PROJECT_ID)
        logger.info(f"✅ 생성된 동영상 GCS에 업로드 완료: {gcs_path}")

        # YouTube 업로드 전에 GCS에서 다시 다운로드하는 과정은
        # Cloud Run 내부에서 로컬 경로로 바로 처리하므로 불필요할 수 있습니다.
        # 하지만 안정성을 위해 유지할 수도 있습니다. 여기서는 유지합니다.
        downloaded_path = f"/tmp/downloaded_{os.path.basename(video_path)}"
        download_from_gcs(GCP_BUCKET_NAME, gcs_path, downloaded_path, GCP_PROJECT_ID)
        logger.info(f"✅ GCS에서 동영상 다운로드 완료: {downloaded_path}")

        upload_video_to_youtube(
            YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN,
            downloaded_path, title, script
        )
        logger.info("✅ YouTube Shorts 업로드 완료.")
    except Exception as e:
        logger.error(f"❌ Shorts 업로드 실패: {e}", exc_info=True)
    finally:
        # 임시 파일 정리 (성공/실패 여부와 관계없이)
        for temp_file in [audio_path, img_path, video_path, downloaded_path]:
            # 파일 경로가 None이 아니고, 파일이 존재하고, 기본 이미지가 아니라면 삭제
            if temp_file and os.path.exists(temp_file) and temp_file != "/app/default_image.jpg":
                try:
                    os.remove(temp_file)
                    logger.info(f"🗑️ 임시 파일 삭제: {temp_file}")
                except OSError as e:
                    logger.warning(f"임시 파일 삭제 실패 '{temp_file}': {e}")


# --- 로컬 실행 진입점 ---
if __name__ == "__main__":
    # Gunicorn에 의해 실행될 때는 이 블록이 실행되지 않습니다.
    # 즉, app.run()은 로컬 개발 환경에서만 사용됩니다.
    # Cloud Run에서는 Gunicorn이 'app' 객체를 직접 실행합니다.
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
