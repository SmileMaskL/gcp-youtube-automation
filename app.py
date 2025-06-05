from flask import Flask, request, jsonify
import os
import time
import logging
import traceback
from threading import Thread
from datetime import datetime, timedelta
from google.cloud import secretmanager

# src 모듈 임포트
from src.video_creator import create_video
from src.youtube_uploader import upload_video
from src.utils import get_trending_topics, clean_old_data
from src.thumbnail_generator import generate_thumbnail
from src.comment_poster import post_comment
from src.shorts_converter import convert_to_shorts

app = Flask(__name__)

# 0. 시작 시 Secret Manager에서 환경변수 설정
def init_secrets():
    """시작 시 모든 비밀 정보 로드"""
    secret_client = secretmanager.SecretManagerServiceClient()
    project_id = os.getenv('GCP_PROJECT_ID')
    
    secrets = {
        'ELEVENLABS_API_KEY': None,
        'GEMINI_API_KEY': None,
        'OPENAI_API_KEYS': None,
        'PEXELS_API_KEY': None,
        'YOUTUBE_CLIENT_SECRET': None,
        'YOUTUBE_REFRESH_TOKEN': None,
        'GCP_SERVICE_ACCOUNT_KEY': None,
        'TRIGGER_ID': None
    }
    
    for key in secrets.keys():
        try:
            name = f"projects/{project_id}/secrets/{key}/versions/latest"
            response = secret_client.access_secret_version(name=name)
            secrets[key] = response.payload.data.decode('UTF-8')
            os.environ[key] = secrets[key]  # 환경변수 설정
            logging.info(f"✅ {key} 로드 완료")
        except Exception as e:
            logging.critical(f"🔴 {key} 로드 실패: {str(e)}")
            raise RuntimeError(f"{key} 로드 실패")

# 초기화 실행
try:
    init_secrets()
except Exception as e:
    logging.critical(f"🔴 시스템 시작 불가: {str(e)}")
    exit(1)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 락 파일 타임아웃 (1시간)
LOCK_TIMEOUT = 3600

@app.route('/run', methods=['POST'])
def run_automation():
    """자동화 작업 트리거 엔드포인트"""
    # 락 파일 체크 (동시 실행 방지)
    if os.path.exists('automation.lock'):
        lock_time = os.path.getmtime('automation.lock')
        if time.time() - lock_time < LOCK_TIMEOUT:
            return jsonify({"status": "error", "message": "이미 실행 중입니다."}), 429
        else:
            os.remove('automation.lock')
    
    # 락 파일 생성
    with open('automation.lock', 'w') as f:
        f.write(str(time.time()))
    
    # 백그라운드 작업 시작
    thread = Thread(target=background_task)
    thread.start()
    
    return jsonify({"status": "started"}), 202

def background_task():
    """실제 자동화 작업 수행"""
    try:
        logger.info("🚀 자동화 작업 시작")
        
        # 1. 인기 주제 가져오기
        topic = get_trending_topics()
        logger.info(f"🔥 선택된 주제: {topic}")
        
        # 2. 콘텐츠 생성
        from src.content_generator import YouTubeAutomation
        generator = YouTubeAutomation()
        generated_content = generator.generate_content(topic)
        logger.info(f"📝 생성된 콘텐츠: {generated_content['title']}")
        
        # 3. 영상 생성
        video_path = create_video(
            script=generated_content['script'],
            output_path=f"videos/{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        )
        logger.info(f"🎥 영상 생성 완료: {video_path}")
        
        # 4. 쇼츠 변환
        shorts_path = convert_to_shorts(video_path)
        logger.info(f"🎬 쇼츠 변환 완료: {shorts_path}")
        
        # 5. 썸네일 생성
        thumbnail_path = generate_thumbnail(generated_content['title'])
        logger.info(f"🖼️ 썸네일 생성 완료: {thumbnail_path}")
        
        # 6. 유튜브 업로드
        video_url = upload_video(
            file_path=shorts_path,
            title=f"{generated_content['title']} │ #Shorts",
            description=(
                f"{generated_content['description']}\n\n"
                "⚠️ 주의: 이 영상은 AI로 자동 생성되었습니다. "
                "실제 사실과 다를 수 있으니 참고용으로만 활용해주세요."
            ),
            thumbnail_path=thumbnail_path
        )
        logger.info(f"📤 업로드 완료: {video_url}")
        
        # 7. 댓글 작성 (옵션)
        if video_url:
            video_id = video_url.split('v=')[1]
            post_comment(video_id, "이 영상이 유익하셨나요? 궁금한 점은 댓글로 남겨주세요! ✨")
            logger.info(f"💬 댓글 작성 완료")
        
        # 8. 정리 작업 (24시간 이상된 파일 삭제)
        clean_old_data(dirs=["videos/", "shorts/", "thumbnails/"], hours=24)
        
    except Exception as e:
        logger.error(f"🔴 백그라운드 작업 실패: {str(e)}\n{traceback.format_exc()}")
    finally:
        # 락 파일 제거
        if os.path.exists('automation.lock'):
            os.remove('automation.lock')
        logger.info("🔚 작업 종료")

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8080, threaded=True)
