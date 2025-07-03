# src/app.py

import os
import logging
import uuid
import tempfile
from datetime import datetime
from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor

# Flask app 선언
app = Flask(__name__)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("✅ 애플리케이션 로깅이 기본 설정되었습니다.")

# ThreadPoolExecutor 초기화
max_app_threads = int(os.getenv('MAX_THREADS', 2))
executor = ThreadPoolExecutor(max_workers=max_app_threads)
logger.info(f"ThreadPoolExecutor가 {max_app_threads}개의 스레드로 초기화되었습니다.")

# 상태 추적용 딕셔너리
job_status = {}

# Health Check
@app.route('/healthz')
def health_check():
    logger.info("Health check endpoint hit. (정상)")
    return "ok", 200

# 작업 상태 확인 엔드포인트
@app.route('/status/<job_id>', methods=['GET'])
def get_status(job_id):
    status = job_status.get(job_id, {'status': 'not_found'})
    logger.info(f"Job status requested for ID: {job_id}, status: {status['status']}")
    return jsonify(status), 200

# 메인 POST 엔드포인트
@app.route("/", methods=["POST"])
def main_endpoint():
    data = request.get_json()
    if not data:
        logger.error("JSON payload가 제공되지 않았습니다.")
        return jsonify({"status": "error", "message": "JSON payload가 제공되지 않았습니다"}), 400

    action = data.get('action', '')
    metadata = data.get('metadata', {})

    job_id = str(uuid.uuid4())
    job_status[job_id] = {
        'status': 'queued',
        'metadata': metadata,
        'start_time': datetime.utcnow().isoformat()
    }
    logger.info(f"새 작업이 대기열에 추가되었습니다. Job ID: {job_id}, Action: {action}")

    if action == 'create_and_upload_shorts':
        executor.submit(process_youtube_shorts_upload, metadata, job_id)
        return jsonify({
            "status": "processing",
            "message": "YouTube Shorts 업로드 프로세스 시작됨",
            "job_id": job_id,
            "status_url": f"/status/{job_id}"
        }), 202
    else:
        logger.warning(f"지원되지 않는 액션이 요청되었습니다: {action}")
        return jsonify({"status": "error", "message": f"지원되지 않는 액션: {action}"}), 400

def process_youtube_shorts_upload(metadata, job_id):
    logger.info(f"▶️ [{job_id}] YouTube Shorts 업로드 프로세스 시작")
    job_status[job_id]['status'] = 'processing'

    audio_path = None
    video_path = None

    try:
        # 실제 로직 생략 – 기존 코드 유지
        logger.info(f"✨ [{job_id}] 작업 성공적으로 완료됨.")
        job_status[job_id].update({
            'status': 'completed',
            'end_time': datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error(f"❌ [{job_id}] 업로드 실패: {e}", exc_info=True)
        job_status[job_id].update({
            'status': 'failed',
            'error': str(e),
            'end_time': datetime.utcnow().isoformat()
        })
    finally:
        # 임시 파일 정리 생략 – 기존 코드 유지
        pass

# 로컬 실행용
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    logger.info(f"로컬 개발 서버 시작: http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port)
