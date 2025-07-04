# src/app.py

import os
import logging
import uuid
from datetime import datetime
from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# ✅ 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("✅ 애플리케이션 로깅이 기본 설정되었습니다.")

# ✅ ThreadPoolExecutor 설정
max_app_threads = int(os.getenv('MAX_WORKERS', 4))
executor = ThreadPoolExecutor(max_workers=max_app_threads)
logger.info(f"ThreadPoolExecutor가 {max_app_threads}개의 스레드로 초기화되었습니다.")

# ✅ 작업 상태 저장 딕셔너리
job_status = {}

@app.route('/healthz', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"}), 200

@app.route('/status/<job_id>', methods=['GET'])
def get_status(job_id):
    status = job_status.get(job_id)
    if not status:
        return jsonify({"status": "not_found"}), 404
    return jsonify(status), 200

@app.route("/", methods=["POST"])
def main_endpoint():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "JSON payload가 제공되지 않았습니다"}), 400

    action = data.get('action', '')
    metadata = data.get('metadata', {})

    job_id = str(uuid.uuid4())
    job_status[job_id] = {'status': 'queued', 'metadata': metadata, 'start_time': datetime.utcnow().isoformat()}

    if action == 'create_and_upload_shorts':
        executor.submit(process_youtube_shorts_upload, metadata, job_id)
        return jsonify({
            "status": "processing",
            "job_id": job_id,
            "status_url": f"/status/{job_id}"
        }), 202

    job_status[job_id]['status'] = 'failed'
    job_status[job_id]['error'] = f"지원되지 않는 액션: {action}"
    job_status[job_id]['end_time'] = datetime.utcnow().isoformat()
    return jsonify({"status": "error", "message": f"지원되지 않는 액션: {action}"}), 400

def process_youtube_shorts_upload(metadata, job_id):
    logger.info(f"▶️ [{job_id}] YouTube Shorts 업로드 프로세스 시작")
    job_status[job_id]['status'] = 'processing'
    try:
        # ✅ 실제 유튜브 Shorts 생성 및 업로드 로직 구현 필요
        logger.info(f"✅ [{job_id}] 작업 성공적으로 완료됨.")
        job_status[job_id]['status'] = 'completed'
    except Exception as e:
        job_status[job_id]['status'] = 'failed'
        job_status[job_id]['error'] = str(e)

# ✅ 애플리케이션 종료 시 ThreadPoolExecutor 안전 종료
import atexit
@atexit.register
def shutdown_threadpool():
    executor.shutdown(wait=True)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
