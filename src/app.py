import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor
import shutil
import requests

# --- Flask 애플리케이션 객체 선언 ---
app = Flask(__name__)

@app.route('/healthz')
def health_check():
    return "ok", 200

# --- 로깅 설정 ---
try:
    import google.cloud.logging
    logging_client = google.cloud.logging.Client()
    logging_client.setup_logging()
    logging.info("✅ Google Cloud Logging이 설정되었습니다.")
except Exception as e:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.warning(f"Google Cloud Logging 설정 실패 (일반 로깅 사용): {e}")

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# --- ThreadPoolExecutor 설정 ---
executor = ThreadPoolExecutor(max_workers=os.cpu_count() * 2 if os.cpu_count() else 2)

# --- 전역 변수 및 초기화 ---
MODULE_IMPORT_FAILED = False
INITIALIZATION_ERROR = None
APP_INITIALIZED_SUCCESSFULLY = False

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from google.cloud import storage
    from openai import OpenAI
    from google.generativeai import configure as configure_gemini
    from elevenlabs import set_api_key as set_elevenlabs_key
    from newsapi import NewsApiClient
    from pexels_api import API

    from video_script_generator import generate_script_from_news
    from audio_generator import generate_audio_from_text
    from video_generator import create_video_from_images_and_audio
    from youtube_uploader import upload_video_to_youtube
    from gcs_helper import upload_to_gcs, download_from_gcs
except ImportError as e:
    logger.critical(f"❌ 필수 모듈 임포트 실패: {e}", exc_info=True)
    MODULE_IMPORT_FAILED = True
    INITIALIZATION_ERROR = f"필수 모듈 임포트 실패: {e}"

# --- 필수 환경 변수 로드 ---
def initialize_app_logic():
    global APP_INITIALIZED_SUCCESSFULLY, INITIALIZATION_ERROR
    required_env_vars = [
        'GCP_PROJECT_ID', 'GCP_BUCKET_NAME', 'YOUTUBE_CLIENT_ID', 'YOUTUBE_CLIENT_SECRET',
        'YOUTUBE_REFRESH_TOKEN', 'ELEVENLABS_API_KEY', 'ELEVENLABS_VOICE_ID',
        'OPENAI_API_KEYS', 'GEMINI_API_KEY', 'NEWSAPI_API_KEY', 'PEXELS_API_KEY'
    ]
    missing_vars = []

    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    if missing_vars:
        INITIALIZATION_ERROR = f"필수 환경 변수 누락: {', '.join(missing_vars)}"
        logger.critical(INITIALIZATION_ERROR)
        return

    try:
        storage_client = storage.Client(project=os.getenv('GCP_PROJECT_ID'))
        globals()['bucket'] = storage_client.get_bucket(os.getenv('GCP_BUCKET_NAME'))
        set_elevenlabs_key(os.getenv('ELEVENLABS_API_KEY'))
        configure_gemini(api_key=os.getenv('GEMINI_API_KEY'))
        globals()['OPENAI_API_KEYS'] = [k.strip() for k in os.getenv('OPENAI_API_KEYS').split(',')]
        APP_INITIALIZED_SUCCESSFULLY = True
        logger.info("✅ 앱 초기화 완료.")
    except Exception as e:
        INITIALIZATION_ERROR = f"초기화 실패: {e}"
        logger.critical(INITIALIZATION_ERROR, exc_info=True)

initialize_app_logic()

# --- 메인 엔드포인트 ---
@app.route("/", methods=["POST"])
def main_endpoint():
    if not APP_INITIALIZED_SUCCESSFULLY:
        return jsonify({"status": "error", "message": INITIALIZATION_ERROR}), 500

    data = request.get_json()
    action = data.get('action', '')
    metadata = data.get('metadata', {})

    if action == 'create_and_upload_shorts':
        executor.submit(process_youtube_shorts_upload, metadata)
        return jsonify({"status": "processing", "message": "Shorts 업로드 시작됨"}), 202
    return jsonify({"status": "error", "message": f"지원되지 않는 액션: {action}"}), 400

# --- YouTube Shorts 생성 및 업로드 ---
def process_youtube_shorts_upload(metadata):
    try:
        news_topic = metadata.get('news_topic', 'AI 뉴스')
        script_data = generate_script_from_news(
            os.getenv('NEWSAPI_API_KEY'),
            globals()['OPENAI_API_KEYS'],
            os.getenv('GEMINI_API_KEY'),
            news_topic
        )
        script = script_data.get('script')
        title = script_data.get('title')

        audio_path = f"/tmp/audio_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp3"
        generate_audio_from_text(script, os.getenv('ELEVENLABS_API_KEY'), os.getenv('ELEVENLABS_VOICE_ID'), audio_path)

        pexels = API(os.getenv('PEXELS_API_KEY'))
        pexels.search(news_topic, page=1, results_per_page=1)
        photo = next(iter(pexels.get_entries()), None)
        img_path = f"/tmp/image_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
        if photo:
            with open(img_path, 'wb') as f:
                f.write(requests.get(photo.medium).content)
        else:
            img_path = "/app/default_image.jpg"

        video_path = f"/tmp/video_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp4"
        create_video_from_images_and_audio([img_path], audio_path, video_path)

        gcs_path = f"shorts/{os.path.basename(video_path)}"
        upload_to_gcs(os.getenv('GCP_BUCKET_NAME'), video_path, gcs_path, os.getenv('GCP_PROJECT_ID'))

        downloaded_path = f"/tmp/downloaded_{os.path.basename(video_path)}"
        download_from_gcs(os.getenv('GCP_BUCKET_NAME'), gcs_path, downloaded_path, os.getenv('GCP_PROJECT_ID'))

        upload_video_to_youtube(
            os.getenv('YOUTUBE_CLIENT_ID'),
            os.getenv('YOUTUBE_CLIENT_SECRET'),
            os.getenv('YOUTUBE_REFRESH_TOKEN'),
            downloaded_path,
            title,
            script
        )
        logger.info("✅ Shorts 업로드 완료.")

    except Exception as e:
        logger.error(f"❌ Shorts 업로드 실패: {e}", exc_info=True)
    finally:
        for f in [audio_path, img_path, video_path, downloaded_path]:
            if f and os.path.exists(f) and f != "/app/default_image.jpg":
                os.remove(f)
        for item in os.listdir('/tmp'):
            item_path = os.path.join('/tmp', item)
            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            except Exception as e:
                logger.warning(f"❌ 임시파일 삭제 실패: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
