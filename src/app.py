# app.py (또는 main.py)
import os
from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor
import logging
import google.cloud.logging
from google.cloud import storage # Cloud Storage
# from google.cloud import pubsub_v1 # Pub/Sub은 현재 사용되지 않으므로 필요 시 주석 해제
import json
import time
from datetime import datetime

# Google Cloud Logging 설정
client = google.cloud.logging.Client()
client.setup_logging()
# 기본 로깅 레벨을 INFO로 설정
logging.getLogger().setLevel(logging.INFO) 

# ThreadPoolExecutor를 사용하여 비동기 처리
executor = ThreadPoolExecutor(max_workers=os.cpu_count() * 2) 

# --- 환경 변수 로드 및 필수 변수 검사 함수 ---
def check_env_variables():
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
    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
    
    # OPENAI_API_KEYS는 쉼표로 구분된 문자열이므로, 실제 사용 시에는 리스트로 변환 후 첫 번째 요소가 존재하는지 확인
    openai_keys_str = os.environ.get('OPENAI_API_KEYS', '')
    if not openai_keys_str.strip(): # 공백 문자열도 비어있다고 간주
        missing_vars.append('OPENAI_API_KEYS')

    if missing_vars:
        error_msg = f"❌ 필수 환경 변수가 누락되었습니다: {', '.join(missing_vars)}"
        logging.error(error_msg)
        raise ValueError(error_msg)
    
    # 환경 변수 로드
    global GCP_PROJECT_ID, GCP_BUCKET_NAME, YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, \
           YOUTUBE_REFRESH_TOKEN, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, OPENAI_API_KEYS, \
           GEMINI_API_KEY, NEWSAPI_API_KEY, PEXELS_API_KEY, bucket
           
    GCP_PROJECT_ID = os.environ.get('GCP_PROJECT_ID')
    GCP_BUCKET_NAME = os.environ.get('GCP_BUCKET_NAME')
    YOUTUBE_CLIENT_ID = os.environ.get('YOUTUBE_CLIENT_ID')
    YOUTUBE_CLIENT_SECRET = os.environ.get('YOUTUBE_CLIENT_SECRET')
    YOUTUBE_REFRESH_TOKEN = os.environ.get('YOUTUBE_REFRESH_TOKEN')
    ELEVENLABS_API_KEY = os.environ.get('ELEVENLABS_API_KEY')
    ELEVENLABS_VOICE_ID = os.environ.get('ELEVENLABS_VOICE_ID')
    OPENAI_API_KEYS = os.environ.get('OPENAI_API_KEYS', '').split(',')
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    NEWSAPI_API_KEY = os.environ.get('NEWSAPI_API_KEY')
    PEXELS_API_KEY = os.environ.get('PEXELS_API_KEY')

    # Cloud Storage 클라이언트 초기화
    try:
        storage_client = storage.Client(project=GCP_PROJECT_ID) # 프로젝트 ID 명시
        bucket = storage_client.get_bucket(GCP_BUCKET_NAME)
        logging.info(f"✅ Cloud Storage 버킷 '{GCP_BUCKET_NAME}' 초기화 성공.")
    except Exception as e:
        error_msg = f"❌ Cloud Storage 버킷 초기화 실패: {e}. GCP_BUCKET_NAME: '{GCP_BUCKET_NAME}'"
        logging.error(error_msg)
        raise RuntimeError(error_msg) # 버킷 초기화 실패 시 컨테이너 시작 중단

# 앱 시작 시 환경 변수 검사 및 초기화 수행
try:
    check_env_variables()
except Exception as e:
    # 환경 변수 검사 실패 시, 앱이 시작되지 않도록 합니다.
    logging.critical(f"애플리케이션 초기화 실패: {e}")
    # Flask 앱이 시작되기 전에 종료되도록 sys.exit() 등을 사용할 수 있지만, 
    # Cloud Run은 컨테이너가 성공적으로 시작(포트 리스닝)해야 하므로
    # 대신 /healthz가 에러를 반환하게 하거나, 다른 요청들이 실패하도록 설계합니다.
    # 여기서는 예외를 던져 Gunicorn이 앱을 로드하지 못하게 합니다.
    raise 

app = Flask(__name__)

@app.route('/healthz', methods=['GET'])
def healthz():
    """상태 체크 엔드포인트"""
    # 환경 변수 검사에 실패했다면 건강하지 않은 상태를 반환
    try:
        # 이 시점에서 check_env_variables()가 이미 성공했어야 합니다.
        # 만약 어떤 이유로 필수 변수가 사라진다면 여기에서 다시 체크하여 오류를 반환
        check_env_variables() 
        return "OK", 200
    except Exception as e:
        logging.error(f"Health check failed due to missing environment variables: {e}")
        return f"Not Ready: {e}", 500


@app.route("/", methods=["POST"])
def main_endpoint(): 
    """기본 엔드포인트 (GitHub Actions 호출용)"""
    try:
        # 요청 본문(request body)을 JSON으로 파싱합니다.
        data = request.get_json()
        if not data:
            logging.error("No JSON payload provided.")
            return jsonify({"status": "error", "message": "No JSON payload provided"}), 400
        
        action = data.get('action', '')
        metadata = data.get('metadata', {})
        
        logging.info(f"Received action: {action}")
        logging.info(f"Metadata: {metadata}")

        if action == 'create_and_upload_shorts':
            # 비동기 작업 시작
            # Cloud Run 컨테이너의 Request Timeout을 충분히 확보해야 합니다. (최대 60분)
            # 현재 워크플로우에서 300초(5분) 타임아웃을 사용하므로, 
            # 이 백그라운드 작업이 5분 안에 완료되어야 합니다.
            future = executor.submit(process_youtube_shorts_upload, metadata) # metadata 전달
            logging.info("YouTube Shorts 업로드 프로세스 백그라운드 시작됨.")
            return jsonify({"status": "processing", "message": "YouTube Shorts 업로드 프로세스 시작됨", "jobId": f"shorts-task-{datetime.now().timestamp()}"}), 202
        else:
            logging.warning(f"Unsupported action: {action}")
            return jsonify({"status": "error", "message": f"지원되지 않는 액션: {action}"}), 400
    except Exception as e:
        logging.error(f"메인 엔드포인트 처리 오류: {e}", exc_info=True)
        # Cloud Run 내부에서 발생하는 500 에러를 명확하게 반환하여 디버깅을 돕습니다.
        return jsonify({"status": "error", "message": f"서버 내부 오류: {str(e)}"}), 500


def process_youtube_shorts_upload(metadata):
    """실제 YouTube Shorts 생성 및 업로드 로직"""
    logging.info(f'YouTube Shorts 업로드 프로세스 시작 (백그라운드, metadata: {metadata})')
    start_time = time.time()

    try:
        # 이 단계에서 실제 API 키가 사용 가능한지 다시 확인
        if not all([YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN,
                    ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, OPENAI_API_KEYS[0],
                    GEMINI_API_KEY, NEWSAPI_API_KEY, PEXELS_API_KEY]):
            raise ValueError("하나 이상의 필수 API 키/환경 변수가 누락되었습니다.")
        
        # 1. 뉴스 데이터 수집 (시뮬레이션 -> 실제 구현 예정)
        logging.info("1. 뉴스 데이터 수집 (시뮬레이션)")
        article_title = f"오늘의 AI 뉴스 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        time.sleep(1)

        # 2. AI 스크립트 생성 (시뮬레이션 -> 실제 구현 예정)
        logging.info("2. AI 스크립트 생성 (시뮬레이션)")
        script_text = f"여러분, {article_title}! AI로 생성된 이 쇼츠를 즐겨보세요! (Workflow ID: {metadata.get('workflow_run_id')})"
        time.sleep(2)

        # 3. 음성 생성 및 저장 (시뮬레이션 -> 실제 구현 예정)
        logging.info("3. 음성 생성 및 Cloud Storage 저장 (시뮬레이션)")
        # 실제 저장 로직 필요 (예: blob.upload_from_filename)
        if bucket:
            # 시뮬레이션: 파일 생성 및 업로드
            mock_audio_file = "mock_audio.mp3"
            with open(mock_audio_file, "w") as f:
                f.write("mock audio content")
            blob = bucket.blob(f"audio/{datetime.now().strftime('%Y%m%d%H%M%S')}.mp3")
            blob.upload_from_filename(mock_audio_file)
            logging.info(f"Mock audio uploaded to gs://{GCP_BUCKET_NAME}/audio/...")
            os.remove(mock_audio_file) # 임시 파일 삭제
        else:
            logging.warning("Cloud Storage 버킷이 초기화되지 않아 음성 저장을 건너뜜.")
        time.sleep(3)

        # 4. 비디오 클립 다운로드 및 저장 (시뮬레이션 -> 실제 구현 예정)
        logging.info("4. 비디오 클립 다운로드 및 Cloud Storage 저장 (시뮬레이션)")
        if bucket:
            # 시뮬레이션: 파일 생성 및 업로드
            mock_video_file = "mock_video.mp4"
            with open(mock_video_file, "w") as f:
                f.write("mock video content")
            blob = bucket.blob(f"video/{datetime.now().strftime('%Y%m%d%H%M%S')}.mp4")
            blob.upload_from_filename(mock_video_file)
            logging.info(f"Mock video uploaded to gs://{GCP_BUCKET_NAME}/video/...")
            os.remove(mock_video_file) # 임시 파일 삭제
        else:
            logging.warning("Cloud Storage 버킷이 초기화되지 않아 비디오 저장을 건너뜜.")
        time.sleep(4)

        # 5. 쇼츠 비디오 최종 생성 (시뮬레이션 -> 실제 구현 예정)
        logging.info("5. 쇼츠 비디오 최종 생성 (시뮬레이션)")
        time.sleep(5)

        # 6. YouTube 업로드 (시뮬레이션 -> 실제 구현 예정)
        logging.info("6. YouTube Data API를 사용하여 쇼츠 업로드 (시뮬레이션)")
        time.sleep(6)

        logging.info(f'✅ YouTube Shorts 업로드 프로세스 완료 (시뮬레이션)')

    except Exception as e:
        logging.error(f"❌ YouTube Shorts 업로드 프로세스 오류: {e}", exc_info=True)
        # 실제 서비스에서는 이 오류를 사용자에게 알리거나, 재시도 로직을 구현해야 합니다.
    finally:
        end_time = time.time()
        logging.info(f"⏱ 총 처리 시간: {end_time - start_time:.2f} 초")

# 이 부분을 삭제하거나 주석 처리합니다. Gunicorn이 앱을 실행합니다.
# if __name__ == '__main__':
#     port = int(os.environ.get('PORT', 8080))
#     app.run(host='0.0.0.0', port=port, debug=False)
