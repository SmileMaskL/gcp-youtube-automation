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

# ThreadPoolExecutor를 사용하여 비동기 처리
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

# Cloud Storage 클라이언트 초기화
storage_client = storage.Client()
bucket = storage_client.get_bucket(GCP_BUCKET_NAME)

app = Flask(__name__)

@app.route('/healthz', methods=['GET'])
def healthz():
    """상태 체크 엔드포인트"""
    return "OK", 200

@app.route("/", methods=["POST"])
def main():
    """기본 엔드포인트 (Cloud Scheduler 호출용)"""
    try:
        action = request.json.get('action', '')
        if action == 'create_and_upload_shorts':
            # 비동기 작업 시작
            future = executor.submit(process_youtube_shorts_upload)
            return jsonify({"status": "processing", "message": "YouTube Shorts 업로드 프로세스 시작됨"}), 202
        else:
            return jsonify({"status": "error", "message": "지원되지 않는 액션"}), 400
    except Exception as e:
        logging.error(f"메인 엔드포인트 오류: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/upload-youtube-shorts', methods=['POST'])
def upload_youtube_shorts_trigger():
    """Cloud Scheduler 또는 다른 HTTP 트리거에 의해 호출되는 엔드포인트"""
    logging.info('YouTube Shorts 업로드 프로세스 시작 요청 수신.')
    try:
        future = executor.submit(process_youtube_shorts_upload)
        return jsonify({"status": "processing", "message": "YouTube Shorts 업로드 프로세스가 백그라운드에서 시작되었습니다."}), 202
    except Exception as e:
        logging.error(f"YouTube Shorts 업로드 프로세스 시작 실패: {e}")
        return jsonify({"status": "error", "message": f"업로드 프로세스 시작 중 오류 발생: {e}"}), 500

def process_youtube_shorts_upload():
    """실제 YouTube Shorts 생성 및 업로드 로직"""
    logging.info('YouTube Shorts 업로드 프로세스 시작 (백그라운드)')
    start_time = time.time()

    try:
        # 1. 뉴스 데이터 수집 (시뮬레이션)
        logging.info("1. 뉴스 데이터 수집 (시뮬레이션)")
        article_title = f"오늘의 AI 뉴스 - {datetime.now().strftime('%Y-%m-%d')}"
        time.sleep(1)

        # 2. AI 스크립트 생성 (시뮬레이션)
        logging.info("2. AI 스크립트 생성 (시뮬레이션)")
        script_text = f"여러분, {article_title}! AI로 생성된 이 쇼츠를 즐겨보세요!"
        time.sleep(2)

        # 3. 음성 생성 및 저장 (시뮬레이션)
        logging.info("3. 음성 생성 및 Cloud Storage 저장 (시뮬레이션)")
        time.sleep(3)

        # 4. 비디오 클립 다운로드 및 저장 (시뮬레이션)
        logging.info("4. 비디오 클립 다운로드 및 Cloud Storage 저장 (시뮬레이션)")
        time.sleep(4)

        # 5. 쇼츠 비디오 최종 생성 (시뮬레이션)
        logging.info("5. 쇼츠 비디오 최종 생성 (시뮬레이션)")
        time.sleep(5)

        # 6. YouTube 업로드 (시뮬레이션)
        logging.info("6. YouTube Data API를 사용하여 쇼츠 업로드 (시뮬레이션)")
        time.sleep(6)

        logging.info(f'✅ YouTube Shorts 업로드 프로세스 완료 (시뮬레이션)')

    except Exception as e:
        logging.error(f"❌ YouTube Shorts 업로드 프로세스 오류: {e}", exc_info=True)

    finally:
        end_time = time.time()
        logging.info(f"⏱ 총 처리 시간: {end_time - start_time:.2f} 초")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
