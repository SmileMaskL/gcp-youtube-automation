# src/app.py

import os
import logging
import json
import uuid
import tempfile
from datetime import datetime
from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor

# 모듈 사전 임포트 (성능 최적화)
from video_script_generator import generate_script_from_news
from audio_generator import generate_audio_from_text
from video_generator import create_video_from_images_and_audio
from youtube_uploader import upload_video_to_youtube
from gcs_helper import upload_to_gcs, download_from_gcs

app = Flask(__name__)

# Google Cloud Logging 설정
try:
    import google.cloud.logging
    logging_client = google.cloud.logging.Client()
    logging_client.setup_logging()
    logging.info("✅ Google Cloud Logging이 설정되었습니다.")
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logging.warning("Google Cloud Logging 미설치, 기본 로깅 사용")
except Exception as e:
    logging.basicConfig(level=logging.INFO)
    logging.error(f"Google Cloud Logging 설정 실패: {e}")

logger = logging.getLogger(__name__)

# ThreadPoolExecutor (CPU 코어 수에 맞춰 동적 조정)
max_workers = int(os.getenv('MAX_WORKERS', os.cpu_count() or 4))
executor = ThreadPoolExecutor(max_workers=max_workers)

# 상태 추적용 딕셔너리
job_status = {}

# Health Check
@app.route('/healthz')
def health_check():
    return "ok", 200

# 작업 상태 확인 엔드포인트
@app.route('/status/<job_id>', methods=['GET'])
def get_status(job_id):
    status = job_status.get(job_id, {'status': 'not_found'})
    return jsonify(status), 200

@app.route("/", methods=["POST"])
def main_endpoint():
    data = request.get_json()
    if not data:
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

    if action == 'create_and_upload_shorts':
        executor.submit(process_youtube_shorts_upload, metadata, job_id)
        return jsonify({
            "status": "processing",
            "message": "YouTube Shorts 업로드 프로세스 시작됨",
            "job_id": job_id,
            "status_url": f"/status/{job_id}"
        }), 202
    else:
        return jsonify({"status": "error", "message": f"지원되지 않는 액션: {action}"}), 400

def process_youtube_shorts_upload(metadata, job_id):
    logger.info(f"▶️ [{job_id}] YouTube Shorts 업로드 프로세스 시작")
    job_status[job_id]['status'] = 'processing'
    
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
            logger.warning(f"⚠️ [{job_id}] 지정된 이미지 없음: {img_path}")
            img_path = '/app/default_image.jpg'
            if not os.path.exists(img_path):
                raise FileNotFoundError(f"기본 이미지 '{img_path}'를 찾을 수 없습니다.")

        # 4. 비디오 생성 (임시 디렉토리 사용)
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as video_temp:
            video_path = video_temp.name
        create_video_from_images_and_audio([img_path], audio_path, video_path)
        logger.info(f"🎥 [{job_id}] 비디오 생성 완료: {video_path}")

        # 5. YouTube 업로드 (GCS 단계 생략)
        upload_video_to_youtube(
            video_path, 
            title, 
            script,
            metadata.get('youtube_credentials', {})
        )
        logger.info(f"✅ [{job_id}] YouTube 업로드 완료")

        # 6. GCS 백업 (옵션)
        if os.getenv('ENABLE_GCS_BACKUP', 'false').lower() == 'true':
            gcs_path = f"shorts/{datetime.now().strftime('%Y%m%d')}/{os.path.basename(video_path)}"
            upload_to_gcs(video_path, gcs_path)
            logger.info(f"☁️ [{job_id}] GCS 백업 완료: {gcs_path}")

        # 상태 업데이트
        job_status[job_id].update({
            'status': 'completed',
            'end_time': datetime.utcnow().isoformat(),
            'output_path': video_path
        })

    except Exception as e:
        logger.error(f"❌ [{job_id}] 업로드 실패: {e}", exc_info=True)
        job_status[job_id].update({
            'status': 'failed',
            'error': str(e),
            'end_time': datetime.utcnow().isoformat()
        })
    finally:
        # 임시 파일 정리 (안전한 삭제)
        temp_files = [audio_path, video_path]
        for path in temp_files:
            try:
                if path and os.path.exists(path):
                    os.remove(path)
                    logger.info(f"🗑️ [{job_id}] 임시 파일 삭제됨: {path}")
            except Exception as e:
                logger.error(f"⚠️ [{job_id}] 파일 삭제 실패: {path} - {e}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("DEBUG", "false").lower() == "true")
