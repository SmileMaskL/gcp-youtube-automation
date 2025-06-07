import os
import time
import logging
from flask import Flask, jsonify
from src.youtube_uploader import YouTubeUploader
from src.openai_utils import OpenAIClient
from src.video_generator import generate_video  # 비디오 생성 모듈

app = Flask(__name__)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 전역 클라이언트 초기화
ai_client = OpenAIClient()
youtube_uploader = YouTubeUploader()

def upload_process():
    """실제 업로드 프로세스"""
    try:
        # 1. 콘텐츠 생성
        prompt = "Create a 5-minute YouTube video script about AI automation"
        script = ai_client.generate_content(prompt)
        logger.info("✅ 콘텐츠 생성 완료")
        
        # 2. 비디오 생성
        video_path = generate_video(script)
        logger.info(f"🎬 비디오 생성 완료: {video_path}")
        
        # 3. 업로드 실행
        title = "AI로 자동 생성된 동영상"
        description = "이 동영상은 AI에 의해 자동 생성되었습니다."
        video_url = youtube_uploader.upload_video(
            file_path=video_path,
            title=title,
            description=description,
            thumbnail_path="thumbnail.jpg" if os.path.exists("thumbnail.jpg") else None
        )
        
        logger.info(f"📤 업로드 완료: {video_url}")
        return True
        
    except Exception as e:
        logger.error(f"❌ 업로드 실패: {str(e)}", exc_info=True)
        return False

@app.route('/upload', methods=['POST'])
def upload():
    """업로드 API 엔드포인트"""
    success = upload_process()
    return jsonify({"success": success, "message": "업로드 완료" if success else "업로드 실패"})

@app.route('/health', methods=['GET'])
def health_check():
    """헬스 체크"""
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
