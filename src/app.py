# src/app.py
import os
import logging
import json
import time
from datetime import datetime
from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor

# Google Cloud Imports
import google.cloud.logging
from google.cloud import storage

# Third-party API Clients (실제 서비스 연동 시 주석 해제 및 설치)
# 주의: 이 파일은 시뮬레이션 로직이므로, 실제 API 사용 시에는 관련 라이브러리 설치 및 키 설정 필요
# import requests # 웹 요청용 (뉴스 API, Pexels API 등)
# from openai import OpenAI # OpenAI Python SDK
# from google.generativeai import configure as configure_gemini, GenerativeModel # Gemini Python SDK
# from elevenlabs import set_api_key as set_elevenlabs_key, generate as generate_elevenlabs_audio # ElevenLabs SDK
# from newsapi import NewsApiClient # NewsAPI Python SDK (뉴스 수집)
# from googleapiclient.discovery import build # YouTube Data API client
# from google.oauth2.credentials import Credentials # YouTube OAuth

# Google Cloud Logging 설정
# Cloud Run 환경에서는 자동으로 로그가 Cloud Logging으로 전송되므로,
# 기본 Python logging 모드를 사용하는 것이 좋습니다.
try:
    logging_client = google.cloud.logging.Client()
    logging_client.setup_logging()
    logging.info("✅ Google Cloud Logging이 설정되었습니다.")
except Exception as e:
    logging.warning(f"Google Cloud Logging 설정 실패 (일반 로깅 사용): {e}")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__) # 모듈별 로거 사용 권장
logger.setLevel(logging.INFO)

# --- 전역 변수 선언 (초기화는 initialize_app 함수에서 진행) ---
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
bucket = None # Cloud Storage 버킷 객체
storage_client_instance = None # Cloud Storage 클라이언트 인스턴스

# ThreadPoolExecutor를 사용하여 비동기 처리
executor = ThreadPoolExecutor(max_workers=os.cpu_count() * 2)

# --- 애플리케이션 초기화 함수 ---
def initialize_app():
    """
    애플리케이션 시작 시 필요한 모든 환경 변수를 로드하고,
    외부 서비스(Cloud Storage 등)를 초기화합니다.
    이 함수에서 실패하면 애플리케이션이 정상적으로 시작되지 않습니다.
    """
    global GCP_PROJECT_ID, GCP_BUCKET_NAME, YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, \
           YOUTUBE_REFRESH_TOKEN, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, OPENAI_API_KEYS, \
           GEMINI_API_KEY, NEWSAPI_API_KEY, PEXELS_API_KEY, bucket, storage_client_instance

    logger.info("🚀 애플리케이션 초기화 시작...")

    required_env_vars = [
        'GCP_PROJECT_ID',
        'GCP_BUCKET_NAME',
        'YOUTUBE_CLIENT_ID',
        'YOUTUBE_CLIENT_SECRET',
        'YOUTUBE_REFRESH_TOKEN',
        'ELEVENLABS_API_KEY',
        'ELEVENLABS_VOICE_ID',
        'OPENAI_API_KEYS', # 쉼표로 구분된 문자열로 받을 것임
        'GEMINI_API_KEY',
        'NEWSAPI_API_KEY',
        'PEXELS_API_KEY'
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if var == 'OPENAI_API_KEYS':
            openai_keys_str = os.environ.get(var, '').strip()
            if not openai_keys_str:
                missing_vars.append(var)
            else:
                OPENAI_API_KEYS = openai_keys_str.split(',')
        else:
            value = os.environ.get(var)
            if not value:
                missing_vars.append(var)
            else:
                globals()[var] = value

    if missing_vars:
        error_msg = f"❌ 치명적 오류: 필수 환경 변수가 누락되었습니다: {', '.join(missing_vars)}"
        logger.critical(error_msg)
        raise ValueError(error_msg)

    # Cloud Storage 클라이언트 초기화
    try:
        storage_client_instance = storage.Client(project=GCP_PROJECT_ID)
        bucket = storage_client_instance.get_bucket(GCP_BUCKET_NAME)
        logger.info(f"✅ Cloud Storage 버킷 '{GCP_BUCKET_NAME}' 초기화 및 접근 확인 성공.")
    except Exception as e:
        error_msg = f"❌ 치명적 오류: Cloud Storage 버킷 초기화 또는 접근 실패: {e}. GCP_BUCKET_NAME: '{GCP_BUCKET_NAME}'"
        logger.critical(error_msg)
        raise RuntimeError(error_msg)

    try:
        # 실제 API 클라이언트 초기화 (필요시 주석 해제)
        logger.info("✅ 모든 필수 환경 변수 및 외부 서비스 초기화 성공.")
    except Exception as e:
        logger.warning(f"일부 외부 API 클라이언트 초기화 실패 (작업 중 다시 시도될 수 있음): {e}")

# 애플리케이션 시작 시 초기화 함수 실행
try:
    initialize_app()
except Exception as e:
    logger.critical(f"🚨🚨🚨 애플리케이션 초기화에 치명적인 오류 발생. 컨테이너를 시작할 수 없습니다: {e}", exc_info=True)
    exit(1)

app = Flask(__name__)

@app.route('/healthz', methods=['GET'])
def healthz():
    """상태 체크 엔드포인트: Cloud Run이 컨테이너의 준비 상태를 확인하는 데 사용"""
    try:
        if bucket is None:
            logger.error("Health check failed: Cloud Storage 버킷 객체가 초기화되지 않았습니다.")
            return "Not Ready: Cloud Storage bucket not initialized", 500
        
        bucket.reload() # 버킷의 최신 메타데이터를 가져와 연결 상태 확인
        logger.info("✅ Health check successful: Cloud Storage bucket reachable.")
        
        return "OK", 200
    except Exception as e:
        logger.error(f"Health check failed: Cloud Storage 연결 테스트 오류: {e}", exc_info=True)
        return f"Not Ready: Cloud Storage connectivity issue: {e}", 500


@app.route("/", methods=["POST"])
def main_endpoint():
    """기본 엔드포인트 (GitHub Actions 호출용)"""
    try:
        data = request.get_json()
        if not data:
            logger.error("JSON payload가 제공되지 않았습니다.")
            return jsonify({"status": "error", "message": "JSON payload가 제공되지 않았습니다"}), 400
        
        action = data.get('action', '')
        metadata = data.get('metadata', {})
        
        logger.info(f"요청된 액션: {action}")
        logger.info(f"메타데이터: {metadata}")

        if action == 'create_and_upload_shorts':
            # 비동기 작업 시작: 실제 YouTube Shorts 생성 및 업로드 로직은 백그라운드에서 실행
            future = executor.submit(process_youtube_shorts_upload, metadata)
            logger.info("YouTube Shorts 업로드 프로세스가 백그라운드에서 시작되었습니다.")
            return jsonify({"status": "processing", "message": "YouTube Shorts 업로드 프로세스가 시작됨", "jobId": f"shorts-task-{datetime.now().timestamp()}"}), 202
        else:
            logger.warning(f"지원되지 않는 액션: {action}")
            return jsonify({"status": "error", "message": f"지원되지 않는 액션: {action}"}), 400
    except Exception as e:
        logger.error(f"메인 엔드포인트 처리 중 오류 발생: {e}", exc_info=True)
        return jsonify({"status": "error", "message": f"서버 내부 오류: {str(e)}"}), 500


def process_youtube_shorts_upload(metadata):
    """
    실제 YouTube Shorts 생성 및 업로드 로직을 포함하는 함수.
    이 함수는 Cloud Run 요청-응답 주기와 독립적으로 백그라운드에서 실행됩니다.
    """
    logger.info(f'--- YouTube Shorts 업로드 프로세스 시작 (metadata: {metadata}) ---')
    start_time = time.time()

    try:
        if not all([YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN,
                      ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, OPENAI_API_KEYS,
                      GEMINI_API_KEY, NEWSAPI_API_KEY, PEXELS_API_KEY]):
            raise ValueError("하나 이상의 필수 API 키/환경 변수가 누락되었습니다. 작업을 계속할 수 없습니다.")
        if bucket is None:
            raise RuntimeError("Cloud Storage 버킷이 초기화되지 않아 파일을 저장할 수 없습니다.")

        # --- 단계별 시뮬레이션 및 실제 API 연동 준비 ---

        # 1. 뉴스 데이터 수집 (NewsAPI 사용 예시)
        logger.info("1. 뉴스 데이터 수집 중...")
        try:
            # newsapi = NewsApiClient(api_key=NEWSAPI_API_KEY)
            # top_headlines = newsapi.get_top_headlines(q='AI', language='en', country='us')
            # if top_headlines and top_headlines['articles']:
            #       article = top_headlines['articles'][0]
            #       article_title = article.get('title', '새로운 AI 소식')
            #       article_description = article.get('description', '흥미로운 AI 관련 기사입니다.')
            #       logger.info(f"뉴스 수집 완료: '{article_title}'")
            # else:
            #       article_title = "오늘의 AI 뉴스"
            #       article_description = "최신 AI 트렌드에 대한 소식입니다."
            #       logger.warning("NewsAPI에서 뉴스를 가져오지 못했습니다. 기본값 사용.")
            article_title = f"오늘의 최신 AI 소식 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            article_description = "생성형 AI 기술의 발전은 계속되고 있습니다."
            logger.info(f"뉴스 수집 (시뮬레이션): {article_title}")
            time.sleep(2)
        except Exception as e:
            logger.error(f"뉴스 데이터 수집 오류: {e}")
            article_title = "뉴스 없음"
            article_description = "뉴스 수집 실패."

        # 2. AI 스크립트 생성 (GPT-4o 또는 Gemini 사용 예시)
        logger.info("2. AI 스크립트 생성 중...")
        script_text = ""
        try:
            script_text = f"✨ 긴급 속보! {article_title}! AI 기술이 또 한 번 세상을 놀라게 했습니다. 자세한 내용은 쇼츠에서 확인하세요! (ID: {metadata.get('workflow_run_id')})"
            logger.info(f"AI 스크립트 생성 (시뮬레이션): {script_text}")
            time.sleep(3)
        except Exception as e:
            logger.error(f"AI 스크립트 생성 오류: {e}")
            script_text = f"AI 스크립트 생성 실패: {article_title}에 대한 자동화된 쇼츠입니다."

        # 3. 음성 생성 및 저장 (ElevenLabs 사용 예시)
        logger.info("3. 음성 생성 및 Cloud Storage 저장 중...")
        audio_file_name = f"audio_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp3"
        local_audio_path = f"/tmp/{audio_file_name}"
        try:
            with open(local_audio_path, "w") as f:
                f.write("mock audio content for shorts")
            logger.info(f"음성 파일 생성 (시뮬레이션): {local_audio_path}")

            blob = bucket.blob(f"audio/{audio_file_name}")
            blob.upload_from_filename(local_audio_path)
            logger.info(f"✅ 음성 파일 '{audio_file_name}'이 Cloud Storage에 업로드되었습니다.")
            os.remove(local_audio_path)
            time.sleep(2)
        except Exception as e:
            logger.error(f"음성 생성 및 저장 오류: {e}")
            if os.path.exists(local_audio_path): os.remove(local_audio_path)

        # 4. 비디오 클립 다운로드 및 저장 (Pexels API 사용 예시)
        logger.info("4. 비디오 클립 다운로드 및 Cloud Storage 저장 중...")
        video_file_name = f"video_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp4"
        local_video_path = f"/tmp/{video_file_name}"
        try:
            with open(local_video_path, "w") as f:
                f.write("mock video content for shorts")
            logger.info(f"비디오 파일 생성 (시뮬레이션): {local_video_path}")

            blob = bucket.blob(f"video/{video_file_name}")
            blob.upload_from_filename(local_video_path)
            logger.info(f"✅ 비디오 파일 '{video_file_name}'이 Cloud Storage에 업로드되었습니다.")
            os.remove(local_video_path)
            time.sleep(3)
        except Exception as e:
            logger.error(f"비디오 다운로드 및 저장 오류: {e}")
            if os.path.exists(local_video_path): os.remove(local_video_path)

        # 5. 쇼츠 비디오 최종 생성 (MoviePy 등 활용 예정)
        logger.info("5. 쇼츠 비디오 최종 생성 중...")
        final_shorts_name = f"youtube_shorts_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp4"
        local_final_shorts_path = f"/tmp/{final_shorts_name}"
        try:
            with open(local_final_shorts_path, "w") as f:
                f.write("mock final shorts video")
            logger.info(f"최종 쇼츠 비디오 생성 (시뮬레이션): {local_final_shorts_path}")

            blob = bucket.blob(f"shorts/{final_shorts_name}")
            blob.upload_from_filename(local_final_shorts_path)
            logger.info(f"✅ 최종 쇼츠 '{final_shorts_name}'이 Cloud Storage에 업로드되었습니다.")
            os.remove(local_final_shorts_path)
            time.sleep(4)
        except Exception as e:
            logger.error(f"쇼츠 비디오 최종 생성 오류: {e}")
            if os.path.exists(local_final_shorts_path): os.remove(local_final_shorts_path)

        # 6. YouTube 업로드 (YouTube Data API 사용 예시)
        logger.info("6. YouTube Data API를 사용하여 쇼츠 업로드 중...")
        try:
            logger.info(f"YouTube 업로드 (시뮬레이션): 제목='{article_title}', 설명='{script_text}'")
            time.sleep(5)
            logger.info(f'✅ YouTube Shorts 업로드 프로세스 완료 (시뮬레이션)')

        except Exception as e:
            logger.error(f"YouTube 업로드 오류: {e}")

    except Exception as e:
        logger.error(f"❌ YouTube Shorts 업로드 프로세스 전체 오류: {e}", exc_info=True)
    finally:
        end_time = time.time()
        logger.info(f"⏱ 총 처리 시간: {end_time - start_time:.2f} 초")
