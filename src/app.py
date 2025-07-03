# src/app.py

import os
import logging
import json
from datetime import datetime
from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor
import shutil

app = Flask(__name__)

# Google Cloud Logging 설정
try:
    import google.cloud.logging
    logging_client = google.cloud.logging.Client()
    logging_client.setup_logging()
    logging.info("✅ Google Cloud Logging이 설정되었습니다.")
except Exception as e:
    logging.basicConfig(level=logging.INFO)
    logging.warning(f"Google Cloud Logging 설정 실패, 기본 로깅 사용: {e}")

logger = logging.getLogger(__name__)

# ThreadPoolExecutor
executor = ThreadPoolExecutor(max_workers=4)

# Health Check
@app.route('/healthz')
def health_check():
    return "ok", 200

@app.route("/", methods=["POST"])
def main_endpoint():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "JSON payload가 제공되지 않았습니다"}), 400

    action = data.get('action', '')
    metadata = data.get('metadata', {})

    if action == 'create_and_upload_shorts':
        executor.submit(process_youtube_shorts_upload, metadata)
        return jsonify({"status": "processing", "message": "YouTube Shorts 업로드 프로세스 시작됨"}), 202
    else:
        return jsonify({"status": "error", "message": f"지원되지 않는 액션: {action}"}), 400

def process_youtube_shorts_upload(metadata):
    logger.info(f"▶️ YouTube Shorts 업로드 프로세스 시작: {metadata}")

    # 예시: 실제 구현 모듈 import
    from video_script_generator import generate_script_from_news
    from audio_generator import generate_audio_from_text
    from video_generator import create_video_from_images_and_audio
    from youtube_uploader import upload_video_to_youtube
    from gcs_helper import upload_to_gcs, download_from_gcs

    try:
        # 스크립트 생성
        news_topic = metadata.get('news_topic', '최신 기술 뉴스')
        script_data = generate_script_from_news(news_topic)
        script = script_data['script']
        title = script_data['title']

        # 음성 생성
        audio_path = f"/tmp/audio_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp3"
        generate_audio_from_text(script, audio_path)

        # 이미지 다운로드 (예시, 실제 구현 필요)
        img_path = "/app/default_image.jpg"
        if not os.path.exists(img_path):
            raise FileNotFoundError(f"기본 이미지 '{img_path}'를 찾을 수 없습니다.")

        # 비디오 생성
        video_path = f"/tmp/video_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp4"
        create_video_from_images_and_audio([img_path], audio_path, video_path)

        # GCS 업로드
        gcs_path = f"shorts/{os.path.basename(video_path)}"
        upload_to_gcs(video_path, gcs_path)

        # GCS에서 다운로드 후 YouTube 업로드
        downloaded_path = f"/tmp/downloaded_{os.path.basename(video_path)}"
        download_from_gcs(gcs_path, downloaded_path)
        upload_video_to_youtube(downloaded_path, title, script)

        logger.info("✅ YouTube Shorts 업로드 완료")

    except Exception as e:
        logger.error(f"❌ Shorts upload process failed: {e}", exc_info=True)
    finally:
        # 임시 파일 정리
        for path in [audio_path, video_path]:
            if os.path.exists(path):
                os.remove(path)
                logger.info(f"🗑️ Removed temporary file: {path}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
