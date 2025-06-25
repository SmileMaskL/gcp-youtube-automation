# src/main.py

import os
import logging
import random
from datetime import datetime
from flask import Request

import functions_framework

# FFmpeg 경로 설정
FFMPEG_BIN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin")
os.environ["PATH"] += os.pathsep + FFMPEG_BIN_DIR
os.environ["IMAGEIO_FFMPEG_EXE"] = os.path.join(FFMPEG_BIN_DIR, "ffmpeg")

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 내부 모듈 가져오기
from .config import Config
from .youtube_uploader import upload_video
from .ai_manager import generate_niche_content
from .tts_generator import generate_tts_audio
from .video_creator import create_short_video
from .video_editor import edit_video_for_shorts
from .bg_downloader import download_background_video

@functions_framework.http
def trigger_youtube_upload(request: Request):
    """Cloud Functions HTTP Entry Point"""
    logger.info(f"요청 수신: {request.method} {request.path}")

    if request.method == "GET":
        return "✅ YouTube Shorts Cloud Function is healthy!", 200

    if request.method != "POST":
        return "⚠️ Only POST method allowed", 405

    # 환경 변수 체크
    project_id = os.environ.get("GCP_PROJECT_ID")
    bucket_name = os.environ.get("GCP_BUCKET_NAME")

    if not project_id or not bucket_name:
        return "❌ 환경변수 GCP_PROJECT_ID 또는 GCP_BUCKET_NAME 누락", 500

    config = Config(project_id=project_id, bucket_name=bucket_name)
    temp_dir = "/tmp"
    os.makedirs(temp_dir, exist_ok=True)

    try:
        niche_keywords = ["신기한 과학", "건강 상식", "꿀팁", "기술 트렌드"]
        selected_niche = random.choice(niche_keywords)
        ai_model = random.choice(["openai", "gemini"])

        ai_response = generate_niche_content(config, selected_niche, ai_model)
        content = ai_response.get("content", "기본 콘텐츠입니다.")
        title = ai_response.get("title", "AI 유튜브 쇼츠")

        audio_path = os.path.join(temp_dir, "voice.mp3")
        generate_tts_audio(config.get_elevenlabs_api_key(), content,
                           config.elevenlabs_voice_id, audio_path)

        video_path = os.path.join(temp_dir, "bg.mp4")
        download_background_video(config.get_pexels_api_key(), selected_niche, video_path)

        base_video = create_short_video(video_path, audio_path,
                                        os.path.join(temp_dir, "base.mp4"))
        final_video = edit_video_for_shorts(base_video, content, title)
        final_path = os.path.join(temp_dir, "final.mp4")
        os.rename(final_video, final_path)

        response = upload_video(
            final_path, title,
            f"주제: {selected_niche}\n내용: {content}",
            tags=[selected_niche, "AI", "Shorts"], category_id="22",
            privacy_status="public", config_instance=config
        )
        return f"✅ 업로드 완료: Video ID = {response.get('id')}", 200

    except Exception as e:
        logger.error("🔥 오류 발생:", exc_info=True)
        return f"❌ 에러: {e}", 500
