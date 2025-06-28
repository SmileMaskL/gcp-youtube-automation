# app.py (또는 main.py)
import os
from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor
import logging
import google.cloud.logging
from google.cloud import storage, pubsub_v1
import json
import time
from datetime import datetime

# Google Cloud Logging 설정
client = google.cloud.logging.Client()
client.setup_logging()
logging.basicConfig(level=logging.INFO)

# ThreadPoolExecutor를 사용하여 비동기 처리 (Cloud Run의 컨테이너 동시성 고려)
# 단일 컨테이너 내에서 여러 요청을 처리할 때 유용하지만,
# Cloud Run의 인스턴스 동시성을 활용한다면 굳이 필요 없을 수 있습니다.
# 일단은 그대로 둡니다.
executor = ThreadPoolExecutor(max_workers=os.cpu_count() * 2) 

# 환경 변수 로드
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

# Cloud Storage 클라이언트 초기화 (환경 변수 확인 후 초기화)
if GCP_BUCKET_NAME:
    try:
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(GCP_BUCKET_NAME)
    except Exception as e:
        logging.error(f"Cloud Storage 버킷 초기화 실패: {e}")
        bucket = None # 초기화 실패 시 None으로 설정
else:
    logging.warning("GCP_BUCKET_NAME 환경 변수가 설정되지 않았습니다. Cloud Storage 관련 기능이 제한될 수 있습니다.")
    bucket = None

app = Flask(__name__)

@app.route('/healthz', methods=['GET'])
def healthz():
    """상태 체크 엔드포인트"""
    return "OK", 200

@app.route("/", methods=["POST"])
def main_endpoint(): # 함수명 변경: main() -> main_endpoint() (충돌 방지 및 명확성)
    """기본 엔드포인트 (Cloud Scheduler 또는 GitHub Actions 호출용)"""
    try:
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
        return jsonify({"status": "error", "message": str(e)}), 500

# @app.route('/upload-youtube-shorts', methods=['POST']) # 이 엔드포인트는 /와 기능 중복이므로 제거하거나,
# def upload_youtube_shorts_trigger(): # 특별한 목적이 없다면 사용하지 않는 것이 좋습니다.
#     """Cloud Scheduler 또는 다른 HTTP 트리거에 의해 호출되는 엔드포인트"""
#     logging.info('YouTube Shorts 업로드 프로세스 시작 요청 수신.')
#     try:
#         future = executor.submit(process_youtube_shorts_upload)
#         return jsonify({"status": "processing", "message": "YouTube Shorts 업로드 프로세스가 백그라운드에서 시작되었습니다."}), 202
#     except Exception as e:
#         logging.error(f"YouTube Shorts 업로드 프로세스 시작 실패: {e}")
#         return jsonify({"status": "error", "message": f"업로드 프로세스 시작 중 오류 발생: {e}"}), 500

# def process_youtube_shorts_upload(): # 인자 추가: metadata
def process_youtube_shorts_upload(metadata):
    """실제 YouTube Shorts 생성 및 업로드 로직"""
    logging.info(f'YouTube Shorts 업로드 프로세스 시작 (백그라운드, metadata: {metadata})')
    start_time = time.time()

    try:
        # 실제 API 키 환경 변수 사용 여부 확인 (예시)
        if not OPENAI_API_KEYS[0] or not GEMINI_API_KEY:
            logging.error("API 키가 설정되지 않았습니다. AI 스크립트 생성이 불가능합니다.")
            # return 대신 raise Exception 또는 처리 로직 추가
            raise ValueError("필수 API 키가 설정되지 않았습니다.")

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
        time.sleep(3)

        # 4. 비디오 클립 다운로드 및 저장 (시뮬레이션 -> 실제 구현 예정)
        logging.info("4. 비디오 클립 다운로드 및 Cloud Storage 저장 (시뮬레이션)")
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

# 이 부분을 삭제하거나 주석 처리해야 합니다! Gunicorn이 앱을 실행합니다.
# if __name__ == '__main__':
#     port = int(os.environ.get('PORT', 8080))
#     app.run(host='0.0.0.0', port=port, debug=False)
