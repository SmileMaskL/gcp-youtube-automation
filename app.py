from flask import Flask, request, jsonify
import os
import time
import logging
import traceback
from threading import Thread
from datetime import datetime
from google.cloud import secretmanager, storage

# src 모듈 임포트
from src.video_creator import create_video
from src.youtube_uploader import upload_video
from src.utils import get_trending_topics, clean_old_data
from src.thumbnail_generator import generate_thumbnail
from src.comment_poster import post_comment
from src.shorts_converter import convert_to_shorts

app = Flask(__name__)

# 0. Secret Manager에서 환경변수 설정 (무료 한도 내)
def init_secrets():
    """환경변수 로드 (월 10,000회까지 무료)"""
    try:
        secret_client = secretmanager.SecretManagerServiceClient()
        project_id = os.getenv('GCP_PROJECT_ID')
        
        secrets = ['ELEVENLABS_API_KEY', 'GEMINI_API_KEY', 'OPENAI_API_KEYS', 
                   'PEXELS_API_KEY', 'YOUTUBE_CLIENT_SECRET', 'YOUTUBE_REFRESH_TOKEN']
        
        for key in secrets:
            name = f"projects/{project_id}/secrets/{key}/versions/latest"
            response = secret_client.access_secret_version(name=name)
            os.environ[key] = response.payload.data.decode('UTF-8')
            logging.info(f"✅ {key} 로드 완료")
            
    except Exception as e:
        logging.critical(f"🔴 Secret Manager 오류: {str(e)}")
        # 로컬 테스트용 대체 키 (실행용)
        os.environ['GEMINI_API_KEY'] = "AIzaSy...D8"  # 실제 무료 Gemini API 키 사용

# 1. 락 파일 관리 (Cloud Storage 버전) - 무료
def create_lock():
    """동시 실행 방지 (GCS 버킷 사용)"""
    client = storage.Client()
    bucket = client.bucket('your-bucket-name')  # GCP 무료 버킷 생성
    blob = bucket.blob('automation.lock')
    
    if blob.exists():
        return False  # 이미 실행 중
    
    blob.upload_from_string(str(time.time()))
    return True

def remove_lock():
    client = storage.Client()
    bucket = client.bucket('your-bucket-name')
    blob = bucket.blob('automation.lock')
    if blob.exists():
        blob.delete()

# 초기화 실행
init_secrets()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.route('/run', methods=['POST'])
def run_automation():
    """자동화 작업 트리거"""
    if not create_lock():
        return jsonify({"status": "error", "message": "이미 실행 중입니다"}), 429
    
    thread = Thread(target=background_task)
    thread.start()
    return jsonify({"status": "시작됨"}), 202

def background_task():
    try:
        logger.info("🚀 작업 시작")
        
        # 1. 인기 주제 가져오기 (무료 Gemini API 사용)
        topic = get_trending_topics()[:1]  # 1개만 선택 (시간 절약)
        
        # 2. 콘텐츠 생성 (무료 GPT-4o/Gemini 사용)
        from src.content_generator import YouTubeAutomation
        generator = YouTubeAutomation()
        generated_content = generator.generate_content(topic)
        generated_content['script'] = generated_content['script'][:500]  # 500자로 제한
        
        # 3. 영상 생성 (60초 고정)
        video_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        video_path = create_video(
            script=generated_content['script'],
            output_path=f"videos/{video_filename}",
            duration=60,  # 60초로 고정 (무료 한도 내)
            resolution="480p" 
        )
        
        # 4. 쇼츠 변환 (9:16 비율)
        shorts_path = convert_to_shorts(video_path)
        
        # 5. 썸네일 생성
        thumbnail_path = generate_thumbnail(generated_content['title'])
        
        # 6. 유튜브 업로드 (수익화 설정 제거)
        video_url = upload_video(
            file_path=shorts_path,
            title=f"{generated_content['title']} │ #Shorts",
            description="AI 생성 콘텐츠입니다",
            thumbnail_path=thumbnail_path
        )
        
        # 7. 댓글 작성 생략 (무료 한도 초과 우려)
        
        # 8. 파일 정리
        clean_old_data(dirs=["videos/", "shorts/", "thumbnails/"], hours=24)
        
    except Exception as e:
        logger.error(f"🔴 오류 발생: {str(e)}")
    finally:
        remove_lock()
        logger.info("🔚 작업 완료")

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8080, threaded=True)
