# src/app.py

import os
import logging
import json
import uuid
import tempfile
from datetime import datetime
from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor

# 모듈 사전 임포트 (성능 최적화 및 초기 오류 감지)
# 이 부분에서 오류가 발생하면 Gunicorn이 앱을 로드하기 전에 컨테이너가 시작되지 못하게 합니다.
try:
    from video_script_generator import generate_script_from_news
    from audio_generator import generate_audio_from_text
    from video_generator import create_video_from_images_and_audio
    from youtube_uploader import upload_video_to_youtube
    from gcs_helper import upload_to_gcs, download_from_gcs
except ImportError as e:
    # 필수 모듈 임포트 실패 시 치명적인 오류로 간주하고 즉시 종료하여
    # Cloud Run이 컨테이너 시작 실패를 명확히 감지하도록 합니다.
    logging.basicConfig(level=logging.CRITICAL)
    logging.critical(f"❌ 필수 모듈 임포트 실패: {e}. 애플리케이션 시작 불가.", exc_info=True)
    exit(1) # 컨테이너를 강제 종료하여 Cloud Run이 문제를 인식하게 함

app = Flask(__name__)

# 로깅 설정 초기화
# Google Cloud Logging 클라이언트 설정 부분은 제거합니다.
# Gunicorn은 기본적으로 표준 출력(stdout/stderr)을 Google Cloud Logging으로 전송하므로,
# Flask 앱 내부에서 google.cloud.logging 클라이언트를 직접 초기화할 필요가 없습니다.
# 이 코드가 오히려 Gunicorn의 로깅 설정과 충돌하거나, Cloud Run 환경에서 인증 문제로 인해
# 앱 시작 실패의 원인이 될 수 있습니다.
logging.basicConfig(level=logging.INFO) # 기본 로거 설정
logger = logging.getLogger(__name__) # 이제 이 logger는 표준 출력으로만 로그를 보냅니다.
logger.info("✅ 애플리케이션 로깅이 기본 설정되었습니다.")


# ThreadPoolExecutor (CPU 코어 수에 맞춰 동적 조정)
# Gunicorn의 --threads 옵션 값과 일치시키거나 그 이상으로 설정하는 것이 좋습니다.
# Dockerfile에 MAX_THREADS 환경 변수를 추가하고 이를 사용하도록 변경합니다.
max_app_threads = int(os.getenv('MAX_THREADS', 2)) # Dockerfile의 --threads 기본값에 맞춰 2로 설정
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

@app.route("/", methods=["POST"])
def main_endpoint():
    data = request.get_json()
    if not data:
        logger.error("JSON payload가 제공되지 않았습니다.")
        return jsonify({"status": "error", "message": "JSON payload가 제공되지 않았습니다"}), 400

    action = data.get('action', '')
    metadata = data.get('metadata', {})
    
    # 작업 ID 생성
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
        # 1. 스크립트 생성
        news_topic = metadata.get('news_topic', '최신 기술 뉴스')
        script_data = generate_script_from_news(news_topic)
        script = script_data['script']
        title = script_data['title']
        job_status[job_id]['title'] = title
        logger.info(f"📝 [{job_id}] 스크립트 생성 완료: {title}")

        # 2. 음성 생성 (임시 디렉토리 사용)
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as audio_temp:
            audio_path = audio_temp.name
        generate_audio_from_text(script, audio_path)
        logger.info(f"🔊 [{job_id}] 오디오 생성 완료: {audio_path}")

        # 3. 이미지 처리
        img_path = metadata.get('image_path', '/app/default_image.jpg')
        if not os.path.exists(img_path):
            logger.warning(f"⚠️ [{job_id}] 지정된 이미지 없음: {img_path}. 기본 이미지를 사용합니다.")
            img_path = '/app/default_image.jpg'
            if not os.path.exists(img_path):
                # 이 경우는 Dockerfile이 잘못되었을 가능성이 높습니다.
                raise FileNotFoundError(f"기본 이미지 '{img_path}'를 컨테이너 내에서 찾을 수 없습니다.")

        # 4. 비디오 생성 (임시 디렉토리 사용)
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as video_temp:
            video_path = video_temp.name
        create_video_from_images_and_audio([img_path], audio_path, video_path)
        logger.info(f"🎥 [{job_id}] 비디오 생성 완료: {video_path}")

        # 5. YouTube 업로드
        # 실제 Cloud Run 배포 시에는 서비스 계정 권한 또는 Secret Manager를 통해
        # YouTube API 자격 증명을 안전하게 관리해야 합니다.
        upload_video_to_youtube(
            video_path, 
            title, 
            script,
            metadata.get('youtube_credentials', {}) 
        )
        logger.info(f"✅ [{job_id}] YouTube 업로드 완료")

        # 6. GCS 백업 (옵션)
        if os.getenv('ENABLE_GCS_BACKUP', 'false').lower() == 'true':
            gcs_bucket = os.getenv('GCS_BUCKET_NAME') # GCS_BUCKET_NAME 환경 변수 사용
            if not gcs_bucket:
                logger.warning(f"⚠️ [{job_id}] GCS_BUCKET_NAME 환경 변수가 설정되지 않아 GCS 백업을 건너뜜.")
            else:
                gcs_path = f"shorts/{datetime.now().strftime('%Y%m%d')}/{os.path.basename(video_path)}"
                # upload_to_gcs 함수가 버킷 이름을 첫 번째 인자로 받도록 수정되어야 합니다.
                # gcs_helper.py 파일을 확인하여 필요시 함수 시그니처를 조정하세요.
                upload_to_gcs(gcs_bucket, video_path, gcs_path) 
                logger.info(f"☁️ [{job_id}] GCS 백업 완료: gs://{gcs_bucket}/{gcs_path}")

        # 상태 업데이트
        job_status[job_id].update({
            'status': 'completed',
            'end_time': datetime.utcnow().isoformat(),
            'output_path': video_path # 임시 파일이 삭제되므로, 실제 업로드된 YouTube URL 등을 저장하는 것이 더 유용할 수 있습니다.
        })
        logger.info(f"✨ [{job_id}] 작업 성공적으로 완료됨.")

    except Exception as e:
        logger.error(f"❌ [{job_id}] 업로드 실패: {e}", exc_info=True)
        job_status[job_id].update({
            'status': 'failed',
            'error': str(e),
            'end_time': datetime.utcnow().isoformat()
        })
    finally:
        # 임시 파일 정리 (안전한 삭제)
        temp_files_to_clean = []
        if audio_path and os.path.exists(audio_path):
            temp_files_to_clean.append(audio_path)
        if video_path and os.path.exists(video_path):
            temp_files_to_clean.append(video_path)
        
        for path in temp_files_to_clean:
            try:
                os.remove(path)
                logger.info(f"🗑️ [{job_id}] 임시 파일 삭제됨: {path}")
            except Exception as e:
                logger.error(f"⚠️ [{job_id}] 임시 파일 삭제 실패: {path} - {e}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    # Flask의 debug 모드는 프로덕션 환경에 적합하지 않습니다.
    # Cloud Run은 Gunicorn을 통해 실행되므로, 이 __name__ == "__main__" 블록은
    # 로컬에서 `python app.py`로 직접 실행할 때만 동작합니다.
    # Gunicorn 사용 시에는 Gunicorn의 워커가 앱을 로드하므로 이 부분이 실행되지 않습니다.
    logger.info(f"로컬 개발 서버 시작: http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
