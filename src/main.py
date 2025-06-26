# src/main.py

import os
import logging
import random
from datetime import datetime
from flask import Request

import functions_framework

# ⭐ 수정 부분: FFmpeg 경로 설정 및 존재 여부 확인 강화
# Cloud Function 배포 시 src/bin/ffmpeg, src/bin/ffprobe 파일이 포함되어야 함
FFMPEG_BIN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin")
FFMPEG_EXE = os.path.join(FFMPEG_BIN_DIR, "ffmpeg")
FFPROBE_EXE = os.path.join(FFMPEG_BIN_DIR, "ffprobe")

# FFmpeg 바이너리 존재 여부 확인 및 환경 변수 설정
if not os.path.exists(FFMPEG_EXE) or not os.path.exists(FFPROBE_EXE):
    logging.error(f"FFmpeg or FFprobe binaries not found in {FFMPEG_BIN_DIR}. Please ensure they are present.")
    # Cloud Function이 제대로 작동하지 않을 수 있으므로 배포 실패를 유도하거나 에러를 명확히 해야 함
    # 실제 운영에서는 sys.exit(1) 또는 raise Exception으로 배포/실행 실패 유도
    # 여기서는 로그만 남기고 일단 진행
else:
    os.environ["PATH"] += os.pathsep + FFMPEG_BIN_DIR
    os.environ["IMAGEIO_FFMPEG_EXE"] = FFMPEG_EXE
    os.environ["IMAGEIO_FFPROBE_EXE"] = FFPROBE_EXE # FFprobe 경로도 명시적으로 설정
    logging.info(f"FFmpeg and FFprobe paths set: {FFMPEG_EXE}, {FFPROBE_EXE}")

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 내부 모듈 가져오기 (⭐ 이 파일들이 src 디렉토리에 모두 존재해야 합니다!)
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
        logger.error("❌ 환경변수 GCP_PROJECT_ID 또는 GCP_BUCKET_NAME 누락")
        return "❌ 환경변수 GCP_PROJECT_ID 또는 GCP_BUCKET_NAME 누락", 500

    config = Config(project_id=project_id, bucket_name=bucket_name)
    temp_dir = "/tmp"
    os.makedirs(temp_dir, exist_ok=True)

    try:
        # ⭐ 수익 최적화 및 무료 한도 고려:
        # 매일 다양한 주제를 생성하여 더 많은 잠재 시청자에게 도달
        niche_keywords = [
            "신기한 과학", "건강 상식", "꿀팁", "기술 트렌드", "역사적 사실",
            "재미있는 심리", "일상 생활 해킹", "동물 이야기", "여행 정보", "미스터리"
        ]
        selected_niche = random.choice(niche_keywords)
        
        # ⭐ AI 모델 선택 최적화:
        # 비용 효율성을 위해 Gemini Free Tier (예: Gemini 1.5 Flash)를 우선 고려.
        # GPT-4o는 더 강력하지만, 무료 한도가 더 제한적일 수 있습니다.
        # 초기에는 하나의 AI 모델로 안정화 후, 나중에 A/B 테스트나 폴백(fallback) 로직 추가 고려
        ai_model = "gemini" # 우선 Gemini로 고정하여 안정성 확보 권장
        # ai_model = random.choice(["openai", "gemini"]) # 두 모델 모두 사용하려면 각 API의 한도를 철저히 모니터링해야 합니다.

        logger.info(f"선택된 니치: {selected_niche}, AI 모델: {ai_model}")
        ai_response = generate_niche_content(config, selected_niche, ai_model)
        content = ai_response.get("content", "").strip() # 공백 제거
        title = ai_response.get("title", "").strip() # 공백 제거

        if not content or not title or len(content) < 20 or len(title) < 5: # 최소 길이 확인
            logger.error(f"AI 콘텐츠 생성 실패: 내용 부족 또는 형식 오류. Content: '{content[:50]}...', Title: '{title}'")
            return "❌ AI가 유효한 콘텐츠 또는 제목을 생성하지 못했습니다. (내용 부족)", 500

        audio_path = os.path.join(temp_dir, "voice.mp3")
        generate_tts_audio(config.get_elevenlabs_api_key(), content,
                           config.elevenlabs_voice_id, audio_path)
        logger.info(f"음성 파일 생성 완료: {audio_path}")

        video_path = os.path.join(temp_dir, "bg.mp4")
        download_background_video(config.get_pexels_api_key(), selected_niche, video_path)
        logger.info(f"배경 영상 다운로드 완료: {video_path}")

        # 동영상 생성 및 편집 (MoviePy 사용)
        base_video_output_path = os.path.join(temp_dir, "base.mp4")
        final_video_output_path = os.path.join(temp_dir, "final.mp4")

        # ⭐ 수정 부분: create_short_video와 edit_video_for_shorts가 파일 경로를 반환하도록 가정
        # MoviePy 클립 객체를 반환하는 경우 .write_videofile을 여기서 호출해야 함
        
        # create_short_video 함수는 원본 비디오 경로, 오디오 경로, 최종 출력 경로를 받아
        # 베이스 비디오 파일을 생성하고 그 파일 경로를 반환해야 합니다.
        base_video_result_path = create_short_video(video_path, audio_path, base_video_output_path)
        logger.info(f"기본 영상 생성 완료: {base_video_result_path}")

        # edit_video_for_shorts 함수는 베이스 비디오 파일 경로, 콘텐츠, 제목을 받아
        # 최종 편집된 비디오 파일을 생성하고 그 파일 경로를 반환해야 합니다.
        edited_video_result_path = edit_video_for_shorts(base_video_result_path, content, title)
        logger.info(f"최종 영상 편집 완료: {edited_video_result_path}")
        
        # ⭐ 수정 부분: 최종 파일 이름이 final_path가 아니라 edited_video_result_path
        # os.rename(final_video, final_path) 대신 직접 사용
        
        # 최종 비디오 파일을 지정된 임시 경로로 옮기거나 이름을 변경
        # MoviePy 작업 후 파일이 다른 이름으로 저장될 수 있으므로, 명시적으로 최종 이름을 설정
        if edited_video_result_path != final_video_output_path:
            os.rename(edited_video_result_path, final_video_output_path)
            logger.info(f"Edited video moved to final path: {final_video_output_path}")

        response = upload_video(
            final_video_output_path, title,
            f"주제: {selected_niche}\n내용: {content}\n\n#Shorts #AI #유튜브자동화 #{selected_niche.replace(' ', '')}", # 설명과 태그 더 풍부하게
            tags=[t.strip() for t in title.split()[:3]] + [selected_niche, "AI", "Shorts", "자동화", datetime.now().strftime("%Y%m%d")] + ["YouTubeShorts"], # 태그 다양화
            category_id="22", # Entertainment (대부분의 Shorts에 적합)
            privacy_status="public", # 수익화를 위해 필수
            config_instance=config
        )
        logger.info(f"✅ YouTube 업로드 완료: Video ID = {response.get('id')}")
        return f"✅ 업로드 완료: Video ID = {response.get('id')}", 200

    except Exception as e:
        logger.error(f"🔥 오류 발생: {e}", exc_info=True) # 상세 스택 트레이스 로그
        return f"❌ 에러 발생: {e}", 500
