import functions_framework
import os
import logging
import json
import random
from google.cloud import storage
from datetime import datetime
from config import Config
from youtube_uploader import upload_video
from ai_manager import generate_niche_content
from tts_generator import generate_tts_audio
from video_creator import create_short_video
from video_editor import edit_video_for_shorts
from bg_downloader import download_background_video

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@functions_framework.http
def trigger_youtube_upload(request):
    logger.info("--- Cloud Function 'trigger_youtube_upload' 시작 ---")

    try:
        project_id = os.environ.get("GCP_PROJECT_ID")
        bucket_name = os.environ.get("GCP_BUCKET_NAME")
        config = Config(project_id=project_id, bucket_name=bucket_name)

        gemini_api_key = config.get_gemini_api_key()
        elevenlabs_api_key = config.get_elevenlabs_api_key()
        elevenlabs_voice_id = config.elevenlabs_voice_id
        pexels_api_key = config.get_pexels_api_key()
        
        logger.info("API 키 및 설정 로드 완료.")

    except Exception as e:
        logger.error(f"설정 또는 시크릿 로드 실패: {e}", exc_info=True)
        return f"설정 오류: {str(e)}", 500

    temp_dir = "/tmp"
    os.makedirs(temp_dir, exist_ok=True)
    niche_keywords = ["신기한 과학 사실", "역사 속 숨겨진 이야기", "최신 기술 트렌드", "일상 속 꿀팁", "건강 상식"]
    selected_niche = random.choice(niche_keywords)
    ai_model_preference = random.choice(["gemini", "openai"])
    content_topic = ""
    suggested_title = ""

    try:
        logger.info(f"선택된 틈새 키워드: '{selected_niche}', AI 모델 선호:
