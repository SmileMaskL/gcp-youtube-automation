import os
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# 로컬 개발 환경을 위한 .env 파일 로드
load_dotenv()

# 로깅 설정 (Cloud Run 환경에서 자동으로 통합됨)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask 애플리케이션 인스턴스 생성
app = Flask(__name__)

# 환경 변수 로드 (Cloud Run 배포 시 자동 주입됨)
app.config['GCP_PROJECT_ID'] = os.getenv('GCP_PROJECT_ID')
app.config['GCP_BUCKET_NAME'] = os.getenv('GCP_BUCKET_NAME')
app.config['YOUTUBE_CLIENT_ID'] = os.getenv('YOUTUBE_CLIENT_ID')
app.config['YOUTUBE_CLIENT_SECRET'] = os.getenv('YOUTUBE_CLIENT_SECRET')
app.config['YOUTUBE_REFRESH_TOKEN'] = os.getenv('YOUTUBE_REFRESH_TOKEN')
app.config['ELEVENLABS_API_KEY'] = os.getenv('ELEVENLABS_API_KEY')
app.config['ELEVENLABS_VOICE_ID'] = os.getenv('ELEVENLABS_VOICE_ID')
app.config['OPENAI_API_KEYS'] = os.getenv('OPENAI_API_KEYS')
app.config['GEMINI_API_KEY'] = os.getenv('GEMINI_API_KEY')
app.config['NEWSAPI_API_KEY'] = os.getenv('NEWSAPI_API_KEY')
app.config['PEXELS_API_KEY'] = os.getenv('PEXELS_API_KEY')

# 필요한 경우, 여기서 config.py에서 설정을 로드할 수 있습니다.
# from . import config # 현재 구조에서는 필요 없을 수 있습니다.
# app.config.from_object(config)

# 헬스 체크 엔드포인트 추가 (Cloud Run이 컨테이너 시작 확인용)
@app.route('/healthz', methods=['GET'])
def healthz():
    return "OK", 200

@app.route('/upload-youtube-shorts', methods=['POST'])
def upload_youtube_shorts_endpoint():
    logger.info("YouTube Shorts 업로드 프로세스 시작 요청 수신.")
    try:
        # TODO: 여기에 실제 YouTube Shorts 생성 및 업로드 로직을 구현합니다.
        # 이전에 제공했던 로직을 여기에 통합해야 합니다.
        # 예:
        # from your_shorts_generator_module import generate_and_upload_short
        # generate_and_upload_short(app.config)
        
        logger.info("YouTube Shorts 업로드 프로세스 완료 (임시).")
        return jsonify({"status": "success", "message": "YouTube Shorts process initiated (placeholder)."}), 200
    except Exception as e:
        logger.error(f"YouTube Shorts 업로드 중 오류 발생: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # 로컬에서 실행할 때 사용될 포트 (Cloud Run에서는 PORT 환경 변수 사용)
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
