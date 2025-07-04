import os
import logging
import uuid
from datetime import datetime
from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor
import atexit

# =============================
# Flask app 선언
# =============================
app = Flask(__name__)

# =============================
# 로깅 설정
# =============================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("✅ 애플리케이션 로깅이 기본 설정되었습니다.")

# =============================
# ThreadPoolExecutor 초기화
# =============================
max_app_threads = int(os.getenv('MAX_THREADS', 2))
executor = ThreadPoolExecutor(max_workers=max_app_threads)
logger.info(f"ThreadPoolExecutor가 {max_app_threads}개의 스레드로 초기화되었습니다.")

# =============================
# 상태 추적용 딕셔너리
# =============================
job_status = {}

# =============================
# Health Check
# =============================
@app.route('/healthz', methods=['GET'])
def health_check():
    """
    Kubernetes/GCP Load Balancer health check endpoint.
    """
    logger.info("✅ Health check endpoint hit.")
    return jsonify({"status": "ok"}), 200

# =============================
# 작업 상태 확인 엔드포인트
# =============================
@app.route('/status/<job_id>', methods=['GET'])
def get_status(job_id):
    """
    Returns the current status of a job.
    """
    status = job_status.get(job_id)
    if not status:
        logger.warning(f"❌ Job ID not found: {job_id}")
        return jsonify({"status": "not_found"}), 404

    logger.info(f"🔎 Job status requested for ID: {job_id}, status: {status['status']}")
    return jsonify(status), 200

# =============================
# 메인 POST 엔드포인트
# =============================
@app.route("/", methods=["POST"])
def main_endpoint():
    """
    Main endpoint to trigger background processing jobs.
    """
    data = request.get_json()
    if not data:
        logger.error("❌ JSON payload가 제공되지 않았습니다.")
        return jsonify({"status": "error", "message": "JSON payload가 제공되지 않았습니다"}), 400

    action = data.get('action', '')
    metadata = data.get('metadata', {})

    # Job ID 생성 및 상태 초기화
    job_id = str(uuid.uuid4())
    job_status[job_id] = {
        'status': 'queued',
        'metadata': metadata,
        'start_time': datetime.utcnow().isoformat()
    }
    logger.info(f"📝 새 작업이 대기열에 추가되었습니다. Job ID: {job_id}, Action: {action}")

    # 액션 라우팅
    if action == 'create_and_upload_shorts':
        executor.submit(process_youtube_shorts_upload, metadata, job_id)
        return jsonify({
            "status": "processing",
            "message": "YouTube Shorts 업로드 프로세스 시작됨",
            "job_id": job_id,
            "status_url": f"/status/{job_id}"
        }), 202

    else:
        logger.warning(f"⚠️ 지원되지 않는 액션이 요청되었습니다: {action}")
        job_status[job_id]['status'] = 'failed'
        job_status[job_id]['error'] = f"지원되지 않는 액션: {action}"
        job_status[job_id]['end_time'] = datetime.utcnow().isoformat()

        return jsonify({"status": "error", "message": f"지원되지 않는 액션: {action}"}), 400

# =============================
# Background Processing Function
# =============================
def process_youtube_shorts_upload(metadata, job_id):
    """
    Background worker to process and upload YouTube Shorts.
    """
    logger.info(f"▶️ [{job_id}] YouTube Shorts 업로드 프로세스 시작")
    job_status[job_id]['status'] = 'processing'

    try:
        # ⭐ 실제 비즈니스 로직 호출 위치 ⭐
        # 예: generate_video(metadata), upload_to_youtube(video_path), 등
        # (여기에 유튜브 쇼츠 생성 및 업로드 관련 코드 구현)

        logger.info(f"✅ [{job_id}] 작업 성공적으로 완료됨.")
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

# =============================
# Graceful shutdown
# =============================
@atexit.register
def shutdown_threadpool():
    logger.info("🛑 ThreadPoolExecutor shutting down...")
    executor.shutdown(wait=True)

# =============================
# 로컬 실행용
# =============================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    logger.info(f"🚀 로컬 개발 서버 시작: http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port)
