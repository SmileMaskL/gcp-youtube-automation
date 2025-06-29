# src/app.py
import os
import logging
import json
import time
from datetime import datetime
from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor
import sys # sys 모듈 임포트

# --- Flask 애플리케이션 객체 선언 (⭐가장 중요! Gunicorn이 가장 먼저 찾습니다⭐) ---
# 이 'app' 객체가 파일 로드 시점에 정의되어 있어야 Gunicorn이 앱을 시작할 수 있습니다.
app = Flask(__name__)

# --- 로깅 설정 (app 객체 선언 후 바로) ---
# Google Cloud Logging 설정
try:
    import google.cloud.logging
    logging_client = google.cloud.logging.Client()
    logging_client.setup_logging()
    logging.info("✅ Google Cloud Logging이 설정되었습니다.")
except Exception as e:
    # Cloud Logging 설정 실패 시에도 일반 로깅으로 진행
    logging.warning(f"Google Cloud Logging 설정 실패 (일반 로깅 사용): {e}")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# --- 전역 변수 선언 및 초기화 상태 플래그 ---
# 사용자 정의 모듈 임포트 성공 여부 플래그
MODULE_IMPORT_FAILED = False 
# 초기화 시 발생하는 에러 메시지 저장용
INITIALIZATION_ERROR = None 
# 앱의 모든 핵심 요소가 정상적으로 초기화되었는지 여부
APP_INITIALIZED_SUCCESSFULLY = False 

# --- 핵심 로직을 try-except 블록으로 감싸서 초기 오류를 명확히 포착 ---
try:
    # --- 환경 변수 로드 (로컬 개발용) ---
    # Cloud Run에서는 환경 변수가 직접 주입되므로 이 부분은 로컬 개발에서만 작동합니다.
    try:
        from dotenv import load_dotenv
        load_dotenv()
        logger.info("✅ .env 파일 로드 시도 (로컬 개발용).")
    except ImportError:
        logger.warning("python-dotenv 모듈을 찾을 수 없습니다. .env 파일 로드를 건너뛰는 중. (배포 환경에서는 정상)")

    # Google Cloud Imports
    from google.cloud import storage

    # Third-party API Clients
    import requests
    from openai import OpenAI
    from google.generativeai import configure as configure_gemini, GenerativeModel
    from elevenlabs import set_api_key as set_elevenlabs_key, generate as generate_elevenlabs_audio
    from newsapi import NewsApiClient
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    import google.auth.transport.requests
    from pexels_api import API

    # 사용자 정의 모듈 임포트 (src/ 디렉토리에 있는지 확인 필요)
    # 이 부분에서 ImportError가 발생하면, Cloud Run 로그에 명확히 남도록 처리됩니다.
    from video_script_generator import generate_script_from_news
    from audio_generator import generate_audio_from_text
    from video_generator import create_video_from_images_and_audio
    from youtube_uploader import upload_video_to_youtube
    from gcs_helper import upload_to_gcs, download_from_gcs, delete_from_gcs

except ImportError as e:
    logger.critical(f"❌ 치명적 오류: 필수 모듈 임포트 실패 (프로그램 시작 불가): {e}", exc_info=True)
    MODULE_IMPORT_FAILED = True
    INITIALIZATION_ERROR = f"필수 모듈 임포트 실패: {e}"
except Exception as e:
    logger.critical(f"❌ 치명적 오류: 애플리케이션 초기 로딩 중 알 수 없는 오류 발생: {e}", exc_info=True)
    INITIALIZATION_ERROR = f"애플리케이션 초기 로딩 중 알 수 없는 오류: {e}"
    # 이 경우 MODULE_IMPORT_FAILED를 True로 설정하여 health check에서 오류를 반환
    MODULE_IMPORT_FAILED = True


# --- 전역 변수 초기값 (initialize_app_logic 함수에서 os.getenv()를 통해 실제 값으로 채워집니다.) ---
# 위 try-except 블록에서 이미 정의된 경우를 대비하여 None으로 초기화 (선언은 필요)
GCP_PROJECT_ID = None
GCP_BUCKET_NAME = None
YOUTUBE_CLIENT_ID = None
YOUTUBE_CLIENT_SECRET = None
YOUTUBE_REFRESH_TOKEN = None
ELEVENLABS_API_KEY = None
ELEVENLABS_VOICE_ID = None
OPENAI_API_KEYS = [] # 쉼표로 구분된 문자열을 리스트로 변환
GEMINI_API_KEY = None
NEWSAPI_API_KEY = None
PEXELS_API_KEY = None
bucket = None # Cloud Storage 버킷 객체
storage_client_instance = None # Cloud Storage 클라이언트 인스턴스

# ThreadPoolExecutor를 사용하여 비동기 처리
executor = ThreadPoolExecutor(max_workers=os.cpu_count() * 2 if os.cpu_count() else 2)

# --- 애플리케이션 초기화 로직 함수 ---
# 이 함수는 Flask 앱이 완전히 로드된 후에 호출됩니다.
# 여기서 문제가 발생해도 앱이 완전히 종료되지 않고, health check로 상태를 알릴 수 있도록 합니다.
def initialize_app_logic():
    """
    애플리케이션 시작 시 필요한 모든 환경 변수를 로드하고,
    외부 서비스(Cloud Storage 등)를 초기화합니다.
    이 함수에서 실패해도 Flask 앱 자체는 계속 실행될 수 있도록 합니다.
    """
    global GCP_PROJECT_ID, GCP_BUCKET_NAME, YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, \
           YOUTUBE_REFRESH_TOKEN, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, OPENAI_API_KEYS, \
           GEMINI_API_KEY, NEWSAPI_API_KEY, PEXELS_API_KEY, bucket, storage_client_instance, \
           APP_INITIALIZED_SUCCESSFULLY, INITIALIZATION_ERROR

    logger.info("🚀 애플리케이션 초기화 로직 시작...")

    # 핵심 모듈 임포트 자체가 실패했다면, 더 이상 초기화 시도하지 않고 종료
    if MODULE_IMPORT_FAILED:
        logger.critical("핵심 모듈 임포트 실패로 초기화 로직 건너뜀. 앱이 기능하지 않을 것입니다.")
        APP_INITIALIZED_SUCCESSFULLY = False
        return

    required_env_vars = [
        'GCP_PROJECT_ID',
        'GCP_BUCKET_NAME',
        'YOUTUBE_CLIENT_ID',
        'YOUTUBE_CLIENT_SECRET',
        'YOUTUBE_REFRESH_TOKEN',
        'ELEVENLABS_API_KEY',
        'ELEVENLABS_VOICE_ID',
        'OPENAI_API_KEYS',
        'GEMINI_API_KEY',
        'NEWSAPI_API_KEY',
        'PEXELS_API_KEY'
    ]
    
    missing_vars = []
    # 환경 변수 로드
    for var_name in required_env_vars:
        if var_name == 'OPENAI_API_KEYS':
            # OPENAI_API_KEYS는 쉼표로 구분된 문자열이므로 특별 처리
            openai_keys_str = os.getenv(var_name, '').strip()
            if not openai_keys_str:
                missing_vars.append(var_name)
            else:
                OPENAI_API_KEYS.clear() # 기존 리스트를 비우고 다시 채움
                OPENAI_API_KEYS.extend([key.strip() for key in openai_keys_str.split(',') if key.strip()])
                if not OPENAI_API_KEYS: # 쉼표로 구분했지만 실제 유효한 키가 없는 경우
                    missing_vars.append(var_name)
        else:
            value = os.getenv(var_name)
            if not value:
                missing_vars.append(var_name)
            else:
                globals()[var_name] = value # 전역 변수에 값 할당

    if missing_vars:
        INITIALIZATION_ERROR = f"❌ 치명적 오류: 필수 환경 변수가 누락되었습니다: {', '.join(missing_vars)}."
        logger.critical(INITIALIZATION_ERROR)
        APP_INITIALIZED_SUCCESSFULLY = False
        return

    # Cloud Storage 클라이언트 초기화
    try:
        storage_client_instance = storage.Client(project=GCP_PROJECT_ID) # project 명시
        bucket = storage_client_instance.get_bucket(GCP_BUCKET_NAME)
        logger.info(f"✅ Cloud Storage 버킷 '{GCP_BUCKET_NAME}' 초기화 및 접근 확인 성공.")
    except Exception as e:
        INITIALIZATION_ERROR = f"❌ 치명적 오류: Cloud Storage 버킷 초기화 또는 접근 실패: {e}. GCP_BUCKET_NAME: '{GCP_BUCKET_NAME}'"
        logger.critical(INITIALIZATION_ERROR, exc_info=True)
        APP_INITIALIZED_SUCCESSFULLY = False
        return

    # 외부 API 클라이언트 라이브러리 초기화 (키 설정)
    try:
        if ELEVENLABS_API_KEY:
            set_elevenlabs_key(ELEVENLABS_API_KEY)
        else:
            logger.warning("ELEVENLABS_API_KEY가 설정되지 않았습니다. ElevenLabs 기능이 제한됩니다.")
        
        if GEMINI_API_KEY:
            configure_gemini(api_key=GEMINI_API_KEY)
        else:
            logger.warning("GEMINI_API_KEY가 설정되지 않았습니다. Gemini 기능이 제한됩니다.")

        logger.info("✅ 외부 API 키 설정 시도 완료 (ElevenLabs, Gemini).")
    except Exception as e:
        INITIALIZATION_ERROR = f"외부 API 클라이언트 설정 중 오류 발생 (일부 기능 제한될 수 있음): {e}"
        logger.warning(INITIALIZATION_ERROR, exc_info=True)
        APP_INITIALIZED_SUCCESSFULLY = False # 부분 초기화 성공이라도 전체는 실패로 간주
        return

    APP_INITIALIZED_SUCCESSFULLY = True
    logger.info("✅ 모든 필수 환경 변수 및 외부 서비스 초기화 성공.")


# --- 애플리케이션 시작 시 초기화 로직 실행 ---
# Flask 앱 객체 'app'이 정의된 후에 이 초기화 로직을 실행합니다.
# 여기서 오류가 나도 'app' 자체는 살아있으므로 health check가 가능합니다.
initialize_app_logic()
if APP_INITIALIZED_SUCCESSFULLY:
    logger.info("✨ Flask 애플리케이션 초기화 완료.")
else:
    logger.critical(f"🚨🚨🚨 애플리케이션 초기화 실패: {INITIALIZATION_ERROR}. Health check 및 메인 엔드포인트에서 오류 반환 예정.")


# --- 라우트 정의 ---

@app.route('/healthz', methods=['GET'])
def healthz():
    """상태 체크 엔드포인트: Cloud Run이 컨테이너의 준비 상태를 확인하는 데 사용"""
    if MODULE_IMPORT_FAILED:
        logger.error(f"❌ Health check failed: 핵심 모듈 임포트 오류. {INITIALIZATION_ERROR}")
        return f"Not Ready: 핵심 모듈 임포트 오류. {INITIALIZATION_ERROR}", 500
    
    if not APP_INITIALIZED_SUCCESSFULLY:
        logger.error(f"❌ Health check failed: 애플리케이션 초기화 오류. {INITIALIZATION_ERROR}")
        return f"Not Ready: 애플리케이션 초기화 오류: {INITIALIZATION_ERROR}", 500
    
    # 추가적으로, 초기화된 클라이언트가 실제로 작동하는지 가벼운 테스트를 할 수 있습니다.
    try:
        if storage_client_instance is None or bucket is None:
             logger.warning("Health check: Cloud Storage 클라이언트/버킷 객체가 초기화되지 않았습니다. (초기화 오류 플래그 확인 필요)")
             return f"Not Ready: Cloud Storage 클라이언트/버킷 초기화 오류. {INITIALIZATION_ERROR}", 500
        
        # 실제 파일을 만들지 않고, 버킷 접근 권한만 가볍게 확인
        # 예를 들어, storage_client_instance.list_buckets(max_results=1).next() 같은 가벼운 연산 시도
        # 하지만 현재 initialize_app_logic이 성공했으면 연결은 된 것으로 간주
        logger.info("✅ Health check successful: 모든 초기화 및 기본 서비스 연결 확인.")
        return "OK", 200
    except Exception as e:
        logger.error(f"Health check failed: GCS 클라이언트/버킷 접근 테스트 오류 또는 기타 초기화 문제: {e}", exc_info=True)
        return f"Not Ready: GCS 클라이언트/버버킷 접근 테스트 오류 또는 기타 초기화 문제: {e}", 500

@app.route("/", methods=["POST"])
def main_endpoint():
    """기본 엔드포인트 (GitHub Actions 호출용)"""
    if MODULE_IMPORT_FAILED:
        logger.error(f"❌ 요청 처리 불가: 핵심 모듈 임포트 오류. {INITIALIZATION_ERROR}")
        return jsonify({"status": "error", "message": f"핵심 모듈 임포트 오류: {INITIALIZATION_ERROR}"}), 500

    if not APP_INITIALIZED_SUCCESSFULLY:
        logger.error(f"❌ 요청 처리 불가: 애플리케이션 초기화 오류. {INITIALIZATION_ERROR}")
        return jsonify({"status": "error", "message": f"애플리케이션 초기화 오류: {INITIALIZATION_ERROR}"}), 500

    try:
        data = request.get_json()
        if not data:
            logger.error("JSON payload가 제공되지 않았습니다.")
            return jsonify({"status": "error", "message": "JSON payload가 제공되지 않았습니다"}), 400
            
        action = data.get('action', '')
        metadata = data.get('metadata', {})
        
        logger.info(f"요청된 액션: {action}")
        logger.info(f"메타데이터: {json.dumps(metadata)}")

        if action == 'create_and_upload_shorts':
            # 비동기 작업 시작: 실제 YouTube Shorts 생성 및 업로드 로직은 백그라운드에서 실행
            # 여기서 필요한 API 키들을 process_youtube_shorts_upload 함수로 전달
            future = executor.submit(
                process_youtube_shorts_upload, 
                metadata,
                GCP_PROJECT_ID,
                GCP_BUCKET_NAME,
                YOUTUBE_CLIENT_ID,
                YOUTUBE_CLIENT_SECRET,
                YOUTUBE_REFRESH_TOKEN,
                ELEVENLABS_API_KEY,
                ELEVENLABS_VOICE_ID,
                OPENAI_API_KEYS, # 리스트 자체를 전달
                GEMINI_API_KEY,
                NEWSAPI_API_KEY,
                PEXELS_API_KEY
            )
            logger.info("YouTube Shorts 업로드 프로세스가 백그라운드에서 시작되었습니다.")
            return jsonify({"status": "processing", "message": "YouTube Shorts 업로드 프로세스가 시작됨", "jobId": f"shorts-task-{datetime.now().timestamp()}"}), 202
        else:
            logger.warning(f"지원되지 않는 액션: {action}")
            return jsonify({"status": "error", "message": f"지원되지 않는 액션: {action}"}), 400
    except Exception as e:
        logger.error(f"메인 엔드포인트 처리 중 오류 발생: {e}", exc_info=True)
        return jsonify({"status": "error", "message": f"서버 내부 오류: {str(e)}"}), 500


def process_youtube_shorts_upload(metadata, gcp_project_id, gcp_bucket_name, youtube_client_id, youtube_client_secret, 
                                  youtube_refresh_token, elevenlabs_api_key, elevenlabs_voice_id, 
                                  openai_api_keys, gemini_api_key, newsapi_api_key, pexels_api_key):
    """
    실제 YouTube Shorts 생성 및 업로드 로직을 포함하는 함수.
    이 함수는 Cloud Run 요청-응답 주기와 독립적으로 백그라운드에서 실행됩니다.
    모든 필요한 API 키와 설정은 인자로 명시적으로 전달받습니다.
    """
    logger.info(f'--- YouTube Shorts 업로드 프로세스 시작 (metadata: {metadata}) ---')
    start_time = time.time()
    
    # 임시 파일 경로 설정
    temp_dir = "/tmp"
    os.makedirs(temp_dir, exist_ok=True) # Cloud Run은 /tmp를 쓰기 가능한 임시 디렉토리로 제공합니다. 

    # 각 단계에서 생성될 파일 경로 변수 초기화
    script_data = None
    audio_filename = None
    local_audio_path = None
    image_paths = []
    output_video_filename = None
    local_final_shorts_path = None
    downloaded_video_path = None

    try:
        # API 키/환경 변수 유효성 재확인 (방어적 코딩)
        # 이제 인자로 받았으니 여기서 다시 체크
        if not (gcp_project_id and gcp_bucket_name and youtube_client_id and 
                youtube_client_secret and youtube_refresh_token and 
                elevenlabs_api_key and elevenlabs_voice_id and openai_api_keys and 
                gemini_api_key and newsapi_api_key and pexels_api_key):
            raise ValueError("하나 이상의 필수 API 키/환경 변수가 process_youtube_shorts_upload 함수로 제대로 전달되지 않았습니다.")

        # --- 실제 API 연동 및 로직 실행 ---

        # 1. 뉴스 데이터 수집 및 AI 스크립트 생성
        logger.info("1. 뉴스 데이터 수집 및 AI 스크립트 생성 중...")
        try:
            # 전달받은 openai_api_keys 리스트를 사용
            script_data = generate_script_from_news(newsapi_api_key, openai_api_keys, gemini_api_key, news_query="최신 기술 뉴스")
            title = script_data.get('title', f"자동 생성 AI 쇼츠 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            script = script_data.get('script', "이것은 뉴스 스크립트 생성에 문제가 발생하여 자동 생성된 비디오입니다. 최신 AI 기술에 대한 흥미로운 소식을 담고 있습니다.")
            search_keywords = script_data.get('search_keywords', "AI, technology, future")
            logger.info(f"✅ 1단계 완료: 제목 '{title}', 스크립트 및 키워드 생성.")
        except Exception as e:
            logger.error(f"뉴스 데이터 수집 또는 AI 스크립트 생성 오류: {e}", exc_info=True)
            title = f"자동 생성 AI 쇼츠 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            script = "이것은 뉴스 스크립트 생성에 문제가 발생하여 자동 생성된 비디오입니다. 최신 AI 기술에 대한 흥미로운 소식을 담고 있습니다."
            search_keywords = "AI, technology, future"
            logger.warning("뉴스/스크립트 생성 실패: 기본값 사용.")


        # 2. 음성 생성
        logger.info("2. 음성 생성 중...")
        audio_filename = f"audio_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp3"
        local_audio_path = os.path.join(temp_dir, audio_filename)
        try:
            generate_audio_from_text(script, elevenlabs_api_key, elevenlabs_voice_id, local_audio_path)
            logger.info(f"✅ 2단계 완료: 음성 파일 '{local_audio_path}' 생성.")
        except Exception as e:
            logger.error(f"음성 생성 오류: {e}", exc_info=True)
            raise RuntimeError(f"음성 생성 실패: {e}")


        # 3. 비디오 클립/이미지 다운로드 (Pexels 사용)
        logger.info("3. 비디오 클립/이미지 다운로드 중...")
        image_paths = []
        try:
            pexels_api_client = API(pexels_api_key)
            query_for_pexels = search_keywords.split(',')[0].strip() if search_keywords else "technology"
            
            photos = pexels_api_client.search(query=query_for_pexels, per_page=10, orientation='landscape')
            
            if photos.entries:
                for i, photo in enumerate(photos.entries):
                    img_url = photo.src['original']
                    img_filename = f"image_{i}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
                    img_path = os.path.join(temp_dir, img_filename)
                    
                    response = requests.get(img_url, stream=True)
                    response.raise_for_status()
                    with open(img_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    image_paths.append(img_path)
                logger.info(f"✅ 3단계 완료: Pexels에서 {len(image_paths)}개 이미지 다운로드.")
            else:
                logger.warning(f"Pexels에서 '{query_for_pexels}'에 대한 적절한 이미지를 찾을 수 없습니다. 기본 이미지 사용을 시도합니다.")
                # 이미지가 없으면 비디오 생성이 불가능하므로, 여기서 예외를 발생시킵니다.
                raise RuntimeError(f"Pexels에서 이미지를 찾을 수 없습니다: {query_for_pexels}")
        except Exception as e:
            logger.error(f"Pexels 이미지 다운로드 오류: {e}", exc_info=True)
            raise RuntimeError(f"Pexels 이미지 다운로드 실패: {e}")


        # 4. 쇼츠 비디오 최종 생성 (MoviePy 등 활용)
        logger.info("4. 쇼츠 비디오 최종 생성 중...")
        output_video_filename = f"final_youtube_shorts_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp4"
        local_final_shorts_path = os.path.join(temp_dir, output_video_filename)
        
        if not image_paths:
            logger.error("다운로드된 이미지가 없어 비디오 생성을 건너뜁니다.")
            raise RuntimeError("비디오 생성을 위한 이미지가 없습니다. Pexels API 및 쿼리 확인 필요.")

        try:
            create_video_from_images_and_audio(image_paths, local_audio_path, local_final_shorts_path)
            logger.info(f"✅ 4단계 완료: 최종 비디오 '{local_final_shorts_path}' 생성.")
        except Exception as e:
            logger.error(f"쇼츠 비디오 최종 생성 오류: {e}", exc_info=True)
            raise RuntimeError(f"비디오 생성 실패: {e}")


        # 5. 생성된 비디오를 Cloud Storage에 업로드
        logger.info("5. 생성된 비디오를 Cloud Storage에 업로드 중...")
        gcs_video_path = f"shorts/{output_video_filename}"
        try:
            upload_to_gcs(gcp_bucket_name, local_final_shorts_path, gcs_video_path, gcp_project_id)
            logger.info(f"✅ 5단계 완료: 비디오 '{gcs_video_path}'를 Cloud Storage에 업로드 완료.")
        except Exception as e:
            logger.error(f"Cloud Storage 업로드 오류: {e}", exc_info=True)
            raise RuntimeError(f"Cloud Storage 업로드 실패: {e}")


        # 6. YouTube에 업로드
        logger.info("6. YouTube Data API를 사용하여 쇼츠 업로드 중...")
        video_title = title
        video_description = script[:4900] + "..." if len(script) > 5000 else script
        
        # Cloud Storage에서 비디오 다운로드하여 YouTube Uploader에 전달 (필수)
        downloaded_video_path = os.path.join(temp_dir, f"downloaded_{output_video_filename}")
        try:
            download_from_gcs(gcp_bucket_name, gcs_video_path, downloaded_video_path, gcp_project_id)
            logger.info(f"✅ 비디오 '{gcs_video_path}'를 GCS에서 임시 경로 '{downloaded_video_path}'로 다운로드 완료.")
        except Exception as e:
            logger.error(f"Cloud Storage에서 최종 비디오 다운로드 오류: {e}", exc_info=True)
            raise RuntimeError(f"GCS에서 비디오 다운로드 실패: {e}")


        try:
            youtube_uploader_response = upload_video_to_youtube(
                youtube_client_id,
                youtube_client_secret,
                youtube_refresh_token,
                downloaded_video_path,
                video_title,
                video_description,
                ["AI", "shorts", "news", "automation", "tech", "trending"]
            )
            logger.info(f"✅ 6단계 완료: YouTube 업로드 성공! 비디오 ID: {youtube_uploader_response.get('id')}")

        except Exception as e:
            logger.error(f"YouTube 업로드 오류: {e}", exc_info=True)
            raise RuntimeError(f"YouTube 업로드 실패: {e}")

    except Exception as e:
        logger.error(f"❌ YouTube Shorts 업로드 프로세스 전체 오류: {e}", exc_info=True)
    finally:
        end_time = time.time()
        logger.info(f"⏱ 총 처리 시간: {end_time - start_time:.2f} 초")
        
        # 임시 파일 정리 (항상 실행)
        for f in [local_audio_path, local_final_shorts_path, downloaded_video_path] + image_paths:
            if f and os.path.exists(f):
                try:
                    os.remove(f)
                    logger.info(f"임시 파일 삭제 완료: {f}")
                except Exception as e:
                    logger.warning(f"임시 파일 삭제 실패 {f}: {e}")
