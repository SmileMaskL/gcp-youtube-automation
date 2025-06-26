import os
import logging
from flask import Flask, request, jsonify # Flask 임포트
from youtube_uploader import YouTubeUploader
from content_generator import ContentGenerator
from video_editor import VideoEditor
from config import Config
from cleanup_manager import clean_up_old_files # cleanup_manager 임포트

# 로깅 설정 (이전에 설정한 방식 유지)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Flask 애플리케이션 초기화
app = Flask(__name__)

# Config 객체 전역적으로 초기화
# Cloud Run 환경 변수를 통해 project_id와 bucket_name이 전달될 것으로 가정
global_config = Config()

@app.route('/upload-youtube-shorts', methods=['POST'])
def upload_youtube_shorts_trigger():
    """
    Cloud Scheduler 또는 HTTP 요청에 의해 트리거되는 메인 함수.
    YouTube Shorts 생성 및 업로드 프로세스를 시작합니다.
    """
    try:
        logger.info("YouTube Shorts 업로드 프로세스 시작 요청 수신.")
        
        # 이전 실행에서 남은 임시 파일 정리 (매 실행 시작 시)
        clean_up_old_files() 

        # 1. 뉴스 데이터 가져오기 및 콘텐츠 생성
        content_generator = ContentGenerator(global_config)
        news_topic, script, video_tags, video_title = content_generator.generate_youtube_shorts_content()
        logger.info(f"뉴스 토픽: {news_topic}")
        logger.info(f"스크립트: {script[:100]}...") # 스크립트 앞부분만 로깅
        logger.info(f"비디오 제목: {video_title}")

        # 2. 비디오 생성
        video_editor = VideoEditor(global_config)
        video_path, thumbnail_path = video_editor.create_shorts_video(script, news_topic)
        logger.info(f"비디오 생성 완료: {video_path}")
        logger.info(f"썸네일 생성 완료: {thumbnail_path}")

        # 3. YouTube에 업로드
        youtube_uploader = YouTubeUploader(global_config)
        video_id = youtube_uploader.upload_video(video_path, thumbnail_path, video_title, script, video_tags)
        logger.info(f"YouTube Shorts 업로드 성공! 비디오 ID: {video_id}")

        # 모든 작업 완료 후 임시 파일 다시 정리
        clean_up_old_files()

        return jsonify({"status": "success", "message": "YouTube Shorts 업로드 및 정리 완료!", "video_id": video_id}), 200

    except Exception as e:
        logger.error(f"YouTube Shorts 업로드 중 오류 발생: {e}", exc_info=True)
        # 에러 발생 시에도 정리 시도
        clean_up_old_files()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health_check', methods=['GET'])
def health_check():
    """Cloud Run 헬스 체크를 위한 엔드포인트."""
    return "OK", 200

if __name__ == '__main__':
    # Cloud Run은 PORT 환경 변수를 제공합니다.
    port = int(os.environ.get('PORT', 8080))
    # Flask 앱을 해당 포트에서 실행합니다.
    app.run(host='0.0.0.0', port=port, debug=False) # Cloud Run에서는 debug=False 권장
