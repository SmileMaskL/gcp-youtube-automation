import os
import logging
import uuid
from datetime import datetime
from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor
import atexit

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("✅ 애플리케이션 로깅이 기본 설정되었습니다.")

max_app_threads = int(os.getenv('MAX_THREADS', 4))
executor = ThreadPoolExecutor(max_workers=max_app_threads)
logger.info(f"ThreadPoolExecutor가 {max_app_threads}개의 스레드로 초기화되었습니다.")

job_status = {}

@app.route('/healthz', methods=['GET'])
def health_check():
    logger.info("✅ Health check endpoint hit.")
    return jsonify({"status": "ok"}), 200

@app.route('/status/<job_id>', methods=['GET'])
def get_status(job_id):
    status = job_status.get(job_id)
    if not status:
        logger.warning(f"❌ Job ID not found: {job_id}")
        return jsonify({"status": "not_found"}), 404

    logger.info(f"🔎 Job status 요청: {job_id}, 상태: {status['status']}")
    return jsonify(status), 200

@app.route("/", methods=["POST"])
def main_endpoint():
    data = request.get_json()
    if not data:
        logger.error("❌ JSON payload가 제공되지 않았습니다.")
        return jsonify({"status": "error", "message": "JSON payload가 제공되지 않았습니다"}), 400

    action = data.get('action', '')
    metadata = data.get('metadata', {})

    job_id = str(uuid.uuid4())
    job_status[job_id] = {
        'status': 'queued',
        'metadata': metadata,
        'start_time': datetime.utcnow().isoformat()
    }
    logger.info(f"📝 새 작업 대기열 추가: Job ID={job_id}, Action={action}")

    if action == 'create_and_upload_shorts':
        executor.submit(process_youtube_shorts_upload, metadata, job_id)
        return jsonify({
            "status": "processing",
            "message": "YouTube Shorts 업로드 프로세스 시작됨",
            "job_id": job_id,
            "status_url": f"/status/{job_id}"
        }), 202

    else:
        logger.warning(f"⚠️ 지원되지 않는 액션 요청: {action}")
        job_status[job_id].update({
            'status': 'failed',
            'error': f"지원되지 않는 액션: {action}",
            'end_time': datetime.utcnow().isoformat()
        })
        return jsonify({"status": "error", "message": f"지원되지 않는 액션: {action}"}), 400

def process_youtube_shorts_upload(metadata, job_id):
    logger.info(f"▶️ [{job_id}] YouTube Shorts 업로드 프로세스 시작")
    job_status[job_id]['status'] = 'processing'

    try:
        # === 여기서 유튜브 쇼츠 생성/업로드 로직 구현 ===
        # 예: generate_video(), upload_youtube_shorts() 등

        logger.info(f"✅ [{job_id}] 작업 성공 완료")
        job_status[job_id].update({
            'status': 'completed',
            'end_time': datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error(f"❌ [{job_id}] 작업 실패: {e}", exc_info=True)
        job_status[job_id].update({
            'status': 'failed',
            'error': str(e),
            'end_time': datetime.utcnow().isoformat()
        })

@atexit.register
def shutdown_threadpool():
    logger.info("🛑 ThreadPoolExecutor 종료 중...")
    executor.shutdown(wait=True)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    logger.info(f"🚀 로컬 서버 시작: http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port)
