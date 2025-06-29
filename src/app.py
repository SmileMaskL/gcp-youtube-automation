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

# Third-party API Clients (실제 서비스 연동을 위해 주석 해제)
import requests # 웹 요청용 (뉴스 API, Pexels API 등)
from openai import OpenAI # OpenAI Python SDK
from google.generativeai import configure as configure_gemini, GenerativeModel # Gemini Python SDK
from elevenlabs import set_api_key as set_elevenlabs_key, generate as generate_elevenlabs_audio # ElevenLabs SDK
from newsapi import NewsApiClient # NewsAPI Python SDK (뉴스 수집)
from googleapiclient.discovery import build # YouTube Data API client
from google.oauth2.credentials import Credentials # YouTube OAuth
import google.auth.transport.requests # Credential refresh에 필요
from pexels_api import API # Pexels API 클라이언트

# 사용자 정의 모듈 임포트
# ensure these modules are in the same src/ directory
from video_script_generator import generate_script_from_news # NewsAPI, AI 스크립트
from audio_generator import generate_audio_from_text # ElevenLabs
from video_generator import create_video_from_images_and_audio # MoviePy
from youtube_uploader import upload_video_to_youtube # YouTube Data API
from gcs_helper import upload_to_gcs, download_from_gcs, delete_from_gcs # Cloud Storage

# --- 환경 변수 로드 (최상단에서 실행, 로컬 개발용) ---
# Cloud Run에서는 환경 변수가 직접 주입되므로 이 라인은 로컬 개발 환경에서만 유효합니다.
try:
    from dotenv import load_dotenv
    load_dotenv()
    logging.info("✅ .env 파일 로드 시도 (로컬 개발용).")
except ImportError:
    logging.warning("python-dotenv 모듈을 찾을 수 없습니다. .env 파일 로드를 건너뜁니다. (배포 환경에서는 정상)")

# Google Cloud Logging 설정
try:
    logging_client = google.cloud.logging.Client()
    logging_client.setup_logging()
    logging.info("✅ Google Cloud Logging이 설정되었습니다.")
except Exception as e:
    logging.warning(f"Google Cloud Logging 설정 실패 (일반 로깅 사용): {e}")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# --- Flask 애플리케이션 객체 선언 (초기화 함수 호출 전에) ---
app = Flask(__name__) # 💡 수정: Flask 앱 객체를 초기화 함수 호출 전에 먼저 선언합니다.

# --- 전역 변수 선언 (초기화는 initialize_app 함수에서 진행) ---
# 이 변수들은 initialize_app() 함수에서 os.getenv()를 통해 실제 값으로 채워집니다.
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
# Cloud Run의 최대 요청 처리 시간(기본 5분, 최대 60분)을 넘기지 않도록 주의해야 합니다.
# 장시간 작업은 Cloud Tasks + Cloud Functions/Workflows 등으로 분리하는 것이 좋습니다.
executor = ThreadPoolExecutor(max_workers=os.cpu_count() * 2 if os.cpu_count() else 2) # 최소 2개의 워커

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
                OPENAI_API_KEYS.extend([key.strip() for key in openai_keys_str.split(',') if key.strip()])
                if not OPENAI_API_KEYS: # 모든 키가 비어있는 경우
                    missing_vars.append(var)
        else:
            value = os.environ.get(var)
            if not value:
                missing_vars.append(var)
            else:
                globals()[var] = value # 전역 변수에 값 할당

    if missing_vars:
        error_msg = f"❌ 치명적 오류: 필수 환경 변수가 누락되었습니다: {', '.join(missing_vars)}. 컨테이너 시작 불가."
        logger.critical(error_msg)
        raise ValueError(error_msg)

    # Cloud Storage 클라이언트 초기화
    try:
        storage_client_instance = storage.Client(project=GCP_PROJECT_ID)
        bucket = storage_client_instance.get_bucket(GCP_BUCKET_NAME)
        logger.info(f"✅ Cloud Storage 버킷 '{GCP_BUCKET_NAME}' 초기화 및 접근 확인 성공.")
    except Exception as e:
        error_msg = f"❌ 치명적 오류: Cloud Storage 버킷 초기화 또는 접근 실패: {e}. GCP_BUCKET_NAME: '{GCP_BUCKET_NAME}'"
        logger.critical(error_msg, exc_info=True)
        raise RuntimeError(error_msg)

    # 외부 API 클라이언트 라이브러리 초기화 (키 설정)
    # 각 유틸리티 모듈에서 API 클라이언트를 직접 초기화할 수도 있지만,
    # 여기에서 전역으로 키를 설정하는 것도 한 방법입니다.
    # 단, 각 모듈이 이 전역 설정을 따르도록 구현되어 있어야 합니다.
    try:
        set_elevenlabs_key(ELEVENLABS_API_KEY)
        configure_gemini(api_key=GEMINI_API_KEY)
        # OpenAI는 리스트를 순환하며 사용할 수 있도록 OpenAI() 객체 생성을 각 함수 내부에서 처리
        logger.info("✅ 외부 API 키 설정 완료 (ElevenLabs, Gemini).")
    except Exception as e:
        logger.warning(f"외부 API 클라이언트 설정 중 오류 발생 (일부 기능 제한될 수 있음): {e}", exc_info=True)

    logger.info("✅ 모든 필수 환경 변수 및 외부 서비스 초기화 성공.")


# --- 애플리케이션 시작 시 초기화 함수 실행 ---
# Gunicorn이 Flask 앱을 로드할 때 이 부분이 실행됩니다.
try:
    initialize_app()
    logger.info("✨ Flask 애플리케이션 객체 생성 완료.")
except Exception as e:
    logger.critical(f"🚨🚨🚨 애플리케이션 초기화에 치명적인 오류 발생. 컨테이너를 시작할 수 없습니다: {e}", exc_info=True)
    # Cloud Run은 이 exit(1) 코드를 통해 컨테이너 시작 실패를 감지합니다.
    exit(1)


# --- 라우트 정의 ---

@app.route('/healthz', methods=['GET'])
def healthz():
    """상태 체크 엔드포인트: Cloud Run이 컨테이너의 준비 상태를 확인하는 데 사용"""
    try:
        # initialize_app()에서 이미 get_bucket을 했으므로 여기서는 추가적인 확인보다는 OK 반환.
        # initialize_app()에서 오류가 발생하면 이 함수는 호출되지 않습니다.
        logger.info("✅ Health check successful.") # 💡 수정: 헬스 체크 성공 로그 추가
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
        logger.info(f"메타데이터: {json.dumps(metadata)}") # 메타데이터 로깅 시 예쁘게

        if action == 'create_and_upload_shorts':
            # 비동기 작업 시작: 실제 YouTube Shorts 생성 및 업로드 로직은 백그라운드에서 실행
            # Cloud Run은 요청을 빠르게 처리하고 응답을 반환해야 하므로,
            # 장시간 작업은 ThreadPoolExecutor로 분리합니다.
            # 작업이 Cloud Run의 요청 타임아웃(기본 5분, 최대 60분)을 초과하지 않도록 주의.
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
    
    # 임시 파일 경로 설정
    temp_dir = "/tmp"
    # Cloud Run은 /tmp를 쓰기 가능한 임시 디렉토리로 제공합니다.
    # 따라서 os.makedirs는 대부분 필요 없지만, 방어적 코딩으로 유지.
    os.makedirs(temp_dir, exist_ok=True) 

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
        # initialize_app()에서 이미 확인했지만, 런타임 중에도 접근 가능성을 높이기 위함.
        if not (GCP_PROJECT_ID and GCP_BUCKET_NAME and YOUTUBE_CLIENT_ID and 
                YOUTUBE_CLIENT_SECRET and YOUTUBE_REFRESH_TOKEN and 
                ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID and OPENAI_API_KEYS and 
                GEMINI_API_KEY and NEWSAPI_API_KEY and PEXELS_API_KEY and bucket):
            raise ValueError("하나 이상의 필수 API 키/환경 변수 또는 Cloud Storage 버킷이 누락되었거나 유효하지 않습니다. 작업을 계속할 수 없습니다.")

        # --- 실제 API 연동 및 로직 실행 ---

        # 1. 뉴스 데이터 수집 및 AI 스크립트 생성
        logger.info("1. 뉴스 데이터 수집 및 AI 스크립트 생성 중...")
        try:
            # video_script_generator.py의 generate_script_from_news 호출
            script_data = generate_script_from_news(NEWSAPI_API_KEY, OPENAI_API_KEYS, GEMINI_API_KEY, news_query="최신 기술 뉴스")
            title = script_data.get('title', f"자동 생성 AI 쇼츠 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            script = script_data.get('script', "이것은 뉴스 스크립트 생성에 문제가 발생하여 자동 생성된 비디오입니다. 최신 AI 기술에 대한 흥미로운 소식을 담고 있습니다.")
            search_keywords = script_data.get('search_keywords', "AI, technology, future")
            logger.info(f"✅ 1단계 완료: 제목 '{title}', 스크립트 및 키워드 생성.")
        except Exception as e:
            logger.error(f"뉴스 데이터 수집 또는 AI 스크립트 생성 오류: {e}", exc_info=True)
            # 오류 발생 시 기본값으로 대체 (완전히 실패하지 않도록)
            title = f"자동 생성 AI 쇼츠 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            script = "이것은 뉴스 스크립트 생성에 문제가 발생하여 자동 생성된 비디오입니다. 최신 AI 기술에 대한 흥미로운 소식을 담고 있습니다."
            search_keywords = "AI, technology, future"
            logger.warning("뉴스/스크립트 생성 실패: 기본값 사용.")


        # 2. 음성 생성
        logger.info("2. 음성 생성 중...")
        audio_filename = f"audio_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp3"
        local_audio_path = os.path.join(temp_dir, audio_filename)
        try:
            # audio_generator.py의 generate_audio_from_text 호출
            # set_elevenlabs_key는 initialize_app에서 이미 했으므로, 여기서 다시 할 필요 없음
            generate_audio_from_text(script, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, local_audio_path)
            logger.info(f"✅ 2단계 완료: 음성 파일 '{local_audio_path}' 생성.")
        except Exception as e:
            logger.error(f"음성 생성 오류: {e}", exc_info=True)
            raise RuntimeError(f"음성 생성 실패: {e}") # 치명적 오류로 처리


        # 3. 비디오 클립/이미지 다운로드 (Pexels 사용)
        logger.info("3. 비디오 클립/이미지 다운로드 중...")
        image_paths = []
        try:
            pexels_api_client = API(PEXELS_API_KEY)
            # search_keywords가 쉼표로 구분된 문자열일 경우, 첫 번째 키워드만 사용하거나 분리하여 사용
            query_for_pexels = search_keywords.split(',')[0].strip() if search_keywords else "technology"
            
            # Pexels에서 가로(landscape) 이미지 10개 검색
            photos = pexels_api_client.search(query=query_for_pexels, per_page=10, orientation='landscape')
            
            if photos.entries:
                for i, photo in enumerate(photos.entries):
                    img_url = photo.src['original'] # 고화질 이미지
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
                # TODO: 이미지가 없을 경우 대체 이미지 사용 또는 오류 처리 로직 추가
                # 현재는 이미지가 없으면 4단계에서 RuntimeError 발생.
                raise RuntimeError(f"Pexels에서 이미지를 찾을 수 없습니다: {query_for_pexels}") # 이미지 없으면 치명적 오류로 처리
        except Exception as e:
            logger.error(f"Pexels 이미지 다운로드 오류: {e}", exc_info=True)
            raise RuntimeError(f"Pexels 이미지 다운로드 실패: {e}") # 치명적 오류로 처리


        # 4. 쇼츠 비디오 최종 생성 (MoviePy 등 활용)
        logger.info("4. 쇼츠 비디오 최종 생성 중...")
        output_video_filename = f"final_youtube_shorts_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp4"
        local_final_shorts_path = os.path.join(temp_dir, output_video_filename)
        
        if not image_paths:
            logger.error("다운로드된 이미지가 없어 비디오 생성을 건너뜁니다.")
            raise RuntimeError("비디오 생성을 위한 이미지가 없습니다. Pexels API 및 쿼리 확인 필요.")

        try:
            # video_generator.py의 create_video_from_images_and_audio 호출
            create_video_from_images_and_audio(image_paths, local_audio_path, local_final_shorts_path)
            logger.info(f"✅ 4단계 완료: 최종 비디오 '{local_final_shorts_path}' 생성.")
        except Exception as e:
            logger.error(f"쇼츠 비디오 최종 생성 오류: {e}", exc_info=True)
            raise RuntimeError(f"비디오 생성 실패: {e}") # 치명적 오류로 처리


        # 5. 생성된 비디오를 Cloud Storage에 업로드
        logger.info("5. 생성된 비디오를 Cloud Storage에 업로드 중...")
        gcs_video_path = f"shorts/{output_video_filename}"
        try:
            # gcs_helper.py의 upload_to_gcs 호출
            upload_to_gcs(GCP_BUCKET_NAME, local_final_shorts_path, gcs_video_path, GCP_PROJECT_ID)
            logger.info(f"✅ 5단계 완료: 비디오 '{gcs_video_path}'를 Cloud Storage에 업로드 완료.")
        except Exception as e:
            logger.error(f"Cloud Storage 업로드 오류: {e}", exc_info=True)
            raise RuntimeError(f"Cloud Storage 업로드 실패: {e}") # 치명적 오류로 처리


        # 6. YouTube에 업로드
        logger.info("6. YouTube Data API를 사용하여 쇼츠 업로드 중...")
        video_title = title # 뉴스 스크립트에서 생성된 제목 사용
        video_description = script[:4900] + "..." if len(script) > 5000 else script # 스크립트 사용, 최대 5000자
        
        # Cloud Storage에서 비디오 다운로드하여 YouTube Uploader에 전달 (필수)
        downloaded_video_path = os.path.join(temp_dir, f"downloaded_{output_video_filename}")
        try:
            download_from_gcs(GCP_BUCKET_NAME, gcs_video_path, downloaded_video_path, GCP_PROJECT_ID)
            logger.info(f"✅ 비디오 '{gcs_video_path}'를 GCS에서 임시 경로 '{downloaded_video_path}'로 다운로드 완료.")
        except Exception as e:
            logger.error(f"Cloud Storage에서 최종 비디오 다운로드 오류: {e}", exc_info=True)
            raise RuntimeError(f"GCS에서 비디오 다운로드 실패: {e}")


        try:
            # youtube_uploader.py의 upload_video_to_youtube 호출
            youtube_uploader_response = upload_video_to_youtube(
                YOUTUBE_CLIENT_ID,
                YOUTUBE_CLIENT_SECRET,
                YOUTUBE_REFRESH_TOKEN,
                downloaded_video_path, # 다운로드된 로컬 비디오 파일 경로
                video_title,
                video_description,
                ["AI", "shorts", "news", "automation", "tech", "trending"] # 관련 태그
            )
            logger.info(f"✅ 6단계 완료: YouTube 업로드 성공! 비디오 ID: {youtube_uploader_response.get('id')}")
            # 수익 창출 로직은 YouTube 업로드 후 설정하는 부분에 해당합니다.
            # 이는 YouTube API 사용 정책과 계정 상태에 따라 달라지며,
            # YouTube Studio에서 직접 설정하거나 추가 API 호출을 해야 합니다.

        except Exception as e:
            logger.error(f"YouTube 업로드 오류: {e}", exc_info=True)
            raise RuntimeError(f"YouTube 업로드 실패: {e}")

    except Exception as e:
        logger.error(f"❌ YouTube Shorts 업로드 프로세스 전체 오류: {e}", exc_info=True)
        # 이 오류는 Cloud Run 로그에서 명확하게 보일 것입니다.
        # 외부 시스템에 알림을 보내는 로직을 추가할 수 있습니다.
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

# 이 부분은 Gunicorn이 Cloud Run 환경에서 앱을 실행할 때 필요 없습니다.
# Gunicorn이 'app:app' (app.py 파일 내의 'app' 객체)을 찾아 실행합니다.
# if __name__ == '__main__':
#     port = int(os.environ.get('PORT', 8080))
#     app.run(host='0.0.0.0', port=port, debug=True) # debug=True는 개발용, 배포 시에는 False
