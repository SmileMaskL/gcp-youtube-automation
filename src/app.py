# src/app.py
import os
import logging
import json
import time
from datetime import datetime
from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor
import sys
import shutil # ⭐ 추가: 임시 파일 정리 시 필요 ⭐

# --- Flask 애플리케이션 객체 선언 (⭐Gunicorn 진입점⭐) ---
app = Flask(__name__)

# --- 로깅 설정 (app 객체 선언 후 바로) ---
try:
    import google.cloud.logging
    logging_client = google.cloud.logging.Client()
    logging_client.setup_logging()
    logging.info("✅ Google Cloud Logging이 설정되었습니다.")
except Exception as e:
    # Cloud Run 환경에서 Google Cloud Logging 설정이 실패하면 일반 로깅으로 대체
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
    # .env 파일은 로컬 개발용입니다. Cloud Run에서는 환경 변수를 직접 설정합니다.
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

    # 사용자 정의 모듈 (여러분의 파일이름이 이대로라면 문제 없음)
    # 이 모듈들이 src 폴더 내부에 있어야 합니다.
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
        logger.critical("모듈 임포트 실패로 초기화 중단. 앱이 시작되지 않습니다.")
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
        logger.info(f"DEBUG: Checking env var '{var_name}'. Value exists: {value is not None and len(str(value)) > 0}") # 디버그 로그 추가
        
        if var_name == 'OPENAI_API_KEYS':
            if value:
                # ⭐ 중요: OPENAI_API_KEYS 환경 변수가 콤마(,)로 구분되어야 합니다.
                OPENAI_API_KEYS.clear()
                OPENAI_API_KEYS.extend([k.strip() for k in value.split(',') if k.strip()])
                if not OPENAI_API_KEYS:
                    missing_vars.append(var_name)
                    logger.error(f"❌ OPENAI_API_KEYS 환경 변수가 비어있거나 잘못된 형식입니다.") # 오류 로그 추가
            else:
                missing_vars.append(var_name)
                logger.error(f"❌ OPENAI_API_KEYS 환경 변수가 설정되지 않았습니다.") # 오류 로그 추가
        elif not value:
            missing_vars.append(var_name)
            logger.error(f"❌ 필수 환경 변수 '{var_name}'가 설정되지 않았습니다.") # 오류 로그 추가
        else:
            globals()[var_name] = value
            logger.info(f"✅ 환경 변수 '{var_name}' 로드 성공.") # 성공 로그 추가

    if missing_vars:
        INITIALIZATION_ERROR = f"필수 환경 변수 누락 또는 오류: {', '.join(missing_vars)}"
        logger.critical(INITIALIZATION_ERROR + " 앱 초기화 중단.")
        APP_INITIALIZED_SUCCESSFULLY = False
        return

    try:
        logger.info(f"DEBUG: Initializing Cloud Storage client for project '{GCP_PROJECT_ID}' and bucket '{GCP_BUCKET_NAME}'...") # 디버그 로그 추가
        storage_client_instance = storage.Client(project=GCP_PROJECT_ID)
        bucket = storage_client_instance.get_bucket(GCP_BUCKET_NAME)
        logger.info(f"✅ Cloud Storage 버킷 '{GCP_BUCKET_NAME}' 초기화 성공.")
    except Exception as e:
        INITIALIZATION_ERROR = f"Cloud Storage 초기화 실패: {e}. 프로젝트 ID, 버킷 이름, 서비스 계정 권한을 확인하세요." # 오류 메시지 구체화
        logger.critical(INITIALIZATION_ERROR, exc_info=True)
        APP_INITIALIZED_SUCCESSFULLY = False
        return

    try:
        logger.info("DEBUG: Setting up ElevenLabs and Gemini API keys...") # 디버그 로그 추가
        set_elevenlabs_key(ELEVENLABS_API_KEY)
        configure_gemini(api_key=GEMINI_API_KEY) # Google Gemini API 설정
        logger.info("✅ ElevenLabs 및 Gemini API 키 설정 완료.")
    except Exception as e:
        INITIALIZATION_ERROR = f"외부 API 키 설정 실패: {e}. API 키가 유효한지 확인하세요." # 오류 메시지 구체화
        logger.critical(INITIALIZATION_ERROR, exc_info=True) # critical로 변경
        APP_INITIALIZED_SUCCESSFULLY = False
        return

    APP_INITIALIZED_SUCCESSFULLY = True
    logger.info("✅ 앱 초기화 성공. 컨테이너가 트래픽을 받을 준비 완료.")

# 앱 시작 시 초기화 함수 호출
initialize_app_logic()

# --- healthz 엔드포인트 ---
@app.route('/healthz', methods=['GET'])
def healthz():
    if MODULE_IMPORT_FAILED:
        msg = INITIALIZATION_ERROR or "필수 모듈 임포트 실패로 앱이 시작되지 못했습니다."
        logger.error(f"❌ Health Check Failed (Module Import): {msg}")
        return f"Not Ready: {msg}", 500
    elif not APP_INITIALIZED_SUCCESSFULLY:
        msg = INITIALIZATION_ERROR or "앱 초기화에 실패했습니다. 환경 변수 또는 API 키를 확인하세요."
        logger.error(f"❌ Health Check Failed (App Initialization): {msg}")
        return f"Not Ready: {msg}", 500
    logger.info("✅ Health Check OK. App is ready.")
    return "OK", 200

# --- 메인 엔드포인트 ---
@app.route("/", methods=["POST"])
def main_endpoint():
    if MODULE_IMPORT_FAILED:
        msg = INITIALIZATION_ERROR or "필수 모듈 임포트 실패로 앱이 시작되지 못했습니다."
        logger.error(f"❌ Main Endpoint Call Failed (Module Import): {msg}")
        return jsonify({"status": "error", "message": msg}), 500
    elif not APP_INITIALIZED_SUCCESSFULLY:
        msg = INITIALIZATION_ERROR or "앱 초기화에 실패했습니다. 환경 변수 또는 API 키를 확인하세요."
        logger.error(f"❌ Main Endpoint Call Failed (App Initialization): {msg}")
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
        logger.info(f"DEBUG: Generating script from news for topic: '{news_topic}'")
        
        # ⭐ GPT-4o와 Google Gemini를 함께 활용하는 로직 (수익 최적화) ⭐
        # 첫 번째 시도: GPT-4o (OpenAI) 사용
        script_data = {}
        try:
            logger.info("DEBUG: Attempting script generation with GPT-4o (OpenAI)...")
            # OpenAI 클라이언트 초기화 (초기화 실패 시 이 부분에서 오류가 발생할 수 있습니다.)
            openai_client = OpenAI(api_key=OPENAI_API_KEYS[0]) # 첫 번째 키 사용 (로테이션 가능)
            script_data = generate_script_from_news(NEWSAPI_API_KEY, [OPENAI_API_KEYS[0]], None, news_topic)
            logger.info("✅ Script generated with GPT-4o.")
        except Exception as e:
            logger.warning(f"⚠️ GPT-4o 스크립트 생성 실패: {e}. Google Gemini로 재시도합니다.", exc_info=True)
            # 두 번째 시도: Google Gemini (평생 무료 사용 고려) 사용
            try:
                logger.info("DEBUG: Attempting script generation with Google Gemini...")
                script_data = generate_script_from_news(NEWSAPI_API_KEY, None, GEMINI_API_KEY, news_topic)
                logger.info("✅ Script generated with Google Gemini.")
            except Exception as e_gemini:
                logger.error(f"❌ Google Gemini 스크립트 생성마저 실패: {e_gemini}", exc_info=True)
                raise Exception("스크립트 생성에 필요한 모든 AI 모델이 실패했습니다.") # 두 번 다 실패하면 최종 에러
        
        script = script_data.get('script', 'AI 자동 생성 스크립트입니다.')
        title = script_data.get('title', f"AI Shorts {datetime.now().strftime('%Y%m%d%H%M%S')}")
        logger.info(f"✅ Script generated. Title: '{title}', Script (first 50 chars): '{script[:50]}...'")

        audio_path = f"/tmp/audio_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp3"
        logger.info(f"DEBUG: Generating audio to '{audio_path}'")
        generate_audio_from_text(script, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, audio_path)
        logger.info(f"✅ Audio generated successfully.")

        pexels = API(PEXELS_API_KEY)
        search_keywords = script_data.get('search_keywords', 'technology, innovation') 
        logger.info(f"DEBUG: Searching Pexels for keywords: '{search_keywords}'")
        pexels.search(search_keywords, page=1, results_per_page=1)
        photo = next(iter(pexels.get_entries()), None)
        
        if photo:
            img_url = photo.medium
            img_path = f"/tmp/image_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
            logger.info(f"DEBUG: Downloading image from Pexels: '{img_url}' to '{img_path}'")
            with open(img_path, 'wb') as f:
                f.write(requests.get(img_url).content)
            logger.info(f"✅ Pexels image downloaded successfully.")
        else:
            logger.warning("⚠️ Pexels에서 이미지를 찾을 수 없습니다. 기본 이미지를 사용합니다.")
            # ⭐ 중요: 이 'default_image.jpg' 파일은 Dockerfile을 통해 /app/default_image.jpg 경로에 있어야 합니다.
            img_path = "/app/default_image.jpg" 
            if not os.path.exists(img_path):
                raise FileNotFoundError(f"기본 이미지 파일이 '{img_path}' 경로에 없습니다. Dockerfile 및 프로젝트 구조 확인 필요.")
            logger.info(f"✅ Using default image from '{img_path}'.")

        video_path = f"/tmp/video_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp4"
        logger.info(f"DEBUG: Creating video to '{video_path}' from audio and image.")
        create_video_from_images_and_audio([img_path], audio_path, video_path)
        logger.info(f"✅ Video created successfully.")

        gcs_path = f"shorts/{os.path.basename(video_path)}"
        logger.info(f"DEBUG: Uploading video to GCS: '{gcs_path}'")
        upload_to_gcs(GCP_BUCKET_NAME, video_path, gcs_path, GCP_PROJECT_ID)
        logger.info(f"✅ Generated video uploaded to GCS: {gcs_path}")

        downloaded_path = f"/tmp/downloaded_{os.path.basename(video_path)}"
        logger.info(f"DEBUG: Downloading video from GCS for YouTube upload: '{downloaded_path}'")
        download_from_gcs(GCP_BUCKET_NAME, gcs_path, downloaded_path, GCP_PROJECT_ID)
        logger.info(f"✅ Video downloaded from GCS successfully.")

        logger.info(f"DEBUG: Uploading video to YouTube.")
        upload_video_to_youtube(
            YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN,
            downloaded_path, title, script
        )
        logger.info("✅ YouTube Shorts uploaded successfully.")

    except Exception as e:
        logger.error(f"❌ Shorts upload process failed: {e}", exc_info=True)
    finally:
        logger.info("DEBUG: Cleaning up temporary files.")
        for temp_file in [audio_path, img_path, video_path, downloaded_path]:
            if temp_file and os.path.exists(temp_file) and temp_file != "/app/default_image.jpg":
                try:
                    os.remove(temp_file)
                    logger.info(f"🗑️ Cleaned up temporary file: {temp_file}")
                except OSError as e:
                    logger.warning(f"Failed to delete temporary file '{temp_file}': {e}")
        # /tmp 디렉토리 자체 비우기 시도 (moviepy 등이 남길 수 있는 파일)
        for item in os.listdir('/tmp'):
            item_path = os.path.join('/tmp', item)
            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path) # ⭐ shutil 임포트 필요 ⭐
            except Exception as e:
                logger.warning(f'Failed to delete leftover temporary item "{item_path}". Reason: {e}')
        logger.info("DEBUG: Temporary file cleanup complete.")


# --- 로컬 실행 진입점 ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
