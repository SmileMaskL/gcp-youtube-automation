from flask import Flask, request, jsonify
import os
import time
import logging
import traceback
from threading import Thread
from datetime import datetime
from google.cloud import storage

# src 모듈 임포트
from src.video_creator import create_video
from src.youtube_uploader import upload_video, is_channel_monetized  # 수정!
from src.utils import get_trending_topics, clean_old_data
from src.thumbnail_generator import generate_thumbnail
from src.comment_poster import post_comment
from src.shorts_converter import convert_to_shorts

app = Flask(__name__)

# 0. 환경변수 로드 (무료 Gemini 사용)
def init_secrets():
    try:
        # ▼▼▼ 실제 운영시 Secret Manager 활성화 ▼▼▼
        # from google.cloud import secretmanager
        # secret_client = secretmanager.SecretManagerServiceClient()
        # ... (기존 코드) ...
        
        # 테스트용 임시 키 (실행 보장)
        os.environ['GEMINI_API_KEY'] = "AIzaSyBDdPghXTe0ll4otHeYpg1pm7OFkf0yJ-A"  # 무료 키
        os.environ['PEXELS_API_KEY'] = "J5QKAf8vBafkzGTq8thXhm7eRayYGa1cWuTqvlmJneiFUSvfP7R985S2"  # Pexels 무료 키
        logging.info("✅ 테스트 키 로드 완료")
    except Exception as e:
        logging.critical(f"🔴 초기화 오류: {str(e)}")

# 1. 락 파일 관리 (Cloud Storage)
def create_lock():
    client = storage.Client()
    bucket = client.bucket('yt-auto-bucket-001')  # ▼▼▼ 실제 버킷명 변경 필수!
    blob = bucket.blob('lockfile.txt')
    
    if blob.exists():
        lock_time = float(blob.download_as_text())
        if time.time() - lock_time < 3600:  # 1시간 타임아웃
            return False
    blob.upload_from_string(str(time.time()))
    return True

def remove_lock():
    client = storage.Client()
    bucket = client.bucket('youtube-auto-bucket')
    blob = bucket.blob('lockfile.txt')
    if blob.exists():
        blob.delete()

# 초기화
init_secrets()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.route('/run', methods=['POST'])
def run_automation():
    if not create_lock():
        return jsonify({"status": "error", "message": "작업 진행 중"}), 429
    
    Thread(target=background_task).start()
    return jsonify({"status": "시작됨"}), 202

def background_task():
    try:
        logger.info("🚀 작업 시작")
        
        # 1. 주제 선택 (Gemini 무료 API)
        topic = get_trending_topics()[:1][0]  # 첫 번째 주제만 선택
        
        # 2. 콘텐츠 생성 (스크립트 500자 제한)
        from src.content_generator import YouTubeAutomation
        content = YouTubeAutomation().generate_content(topic)
        content['script'] = content['script'][:500]
        
        # 3. 영상 생성 (480p 해상도 강제 설정)
        video_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        video_path = create_video(
            script=content['script'],
            output_path=f"videos/{video_filename}",
            duration=60,
            resolution="480p"  # ▼▼▼ 핵심 추가!
        )
        
        # 4. 쇼츠 변환
        shorts_path = convert_to_shorts(video_path)
        
        # 5. 썸네일 생성
        thumbnail_path = generate_thumbnail(content['title'])
        
        # 6. 유튜브 업로드 (수익화 자동 시도)
        video_url = upload_video(
            file_path=shorts_path,
            title=f"{content['title']} │ #Shorts",
            description="AI 자동 생성 영상",
            thumbnail_path=thumbnail_path
        )
        
        # 7. 파일 정리 (24시간 이상 데이터 삭제)
        clean_old_data(dirs=["videos/", "shorts/", "thumbnails/"], hours=24)
        
    except Exception as e:
        logger.error(f"🔴 오류: {str(e)}")
    finally:
        remove_lock()
        logger.info("🔚 작업 완료")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, threaded=True)
