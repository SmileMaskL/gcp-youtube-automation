# src/main.py

import os
import logging
import random
import tempfile # 임시 파일 생성을 위한 모듈 추가
from datetime import datetime
from typing import Dict, Any # 타입 힌트 추가

import functions_framework # functions_framework.Request 사용을 위해 임포트

# --- 수정 시작: FFmpeg 경로 설정 강화 ---
# Cloud Function 배포 시 src/bin/ffmpeg, src/bin/ffprobe 파일이 포함되어야 함
FFMPEG_BIN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin")
FFMPEG_EXE = os.path.join(FFMPEG_BIN_DIR, "ffmpeg")
FFPROBE_EXE = os.path.join(FFMPEG_BIN_DIR, "ffprobe")

# FFmpeg 바이너리 존재 여부 확인 및 환경 변수 설정
# 중요: MoviePy는 FFMPEG_BINARY 환경 변수를 우선적으로 사용합니다.
if not os.path.exists(FFMPEG_EXE):
    logging.error(f"❌ FFmpeg binary not found at {FFMPEG_EXE}. Please ensure it is present and has execute permissions.")
    raise FileNotFoundError(f"FFmpeg binary missing: {FFMPEG_EXE}")
if not os.path.exists(FFPROBE_EXE):
    logging.error(f"❌ FFprobe binary not found at {FFPROBE_EXE}. Please ensure it is present and has execute permissions.")
    raise FileNotFoundError(f"FFprobe binary missing: {FFPROBE_EXE}")

# MoviePy가 FFmpeg을 찾을 수 있도록 환경 변수 설정
os.environ["FFMPEG_BINARY"] = FFMPEG_EXE
os.environ["FFPROBE_BINARY"] = FFPROBE_EXE # FFprobe 경로도 명시적으로 설정

# PATH 환경 변수에 FFmpeg 바이너리 경로 추가 (안전 장치)
if FFMPEG_BIN_DIR not in os.environ["PATH"]:
    os.environ["PATH"] += os.pathsep + FFMPEG_BIN_DIR

logging.info(f"✅ FFmpeg and FFprobe paths set: FFMPEG_BINARY={os.environ['FFMPEG_BINARY']}, FFPROBE_BINARY={os.environ['FFPROBE_BINARY']}")
# --- 수정 끝: FFmpeg 경로 설정 강화 ---

# 로깅 설정 (Cloud Functions는 기본적으로 Stackdriver Logging으로 전송)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 내부 모듈 가져오기 (⭐ 이 파일들이 src 디렉토리에 모두 존재해야 합니다!)
# .config, .youtube_uploader, .ai_manager, .tts_generator, .video_creator, .video_editor, .bg_downloader
# 이 모듈들이 src/ 폴더 안에 실제로 .py 파일로 존재해야 합니다.
# 예시: src/config.py, src/youtube_uploader.py 등
try:
    from .config import Config
    from .youtube_uploader import upload_video
    from .ai_manager import generate_niche_content
    from .tts_generator import generate_tts_audio
    from .video_creator import create_short_video
    from .video_editor import edit_video_for_shorts
    from .bg_downloader import download_background_video
    logging.info("✅ All custom modules imported successfully.")
except ImportError as e:
    logger.error(f"❌ Custom module import failed: {e}. Please ensure all custom modules are in 'src/' directory.")
    # 모듈 임포트 실패는 치명적이므로, 함수 시작 전에 오류 발생
    raise ImportError(f"Failed to import custom module: {e}")

@functions_framework.http
def trigger_youtube_upload(request: functions_framework.Request) -> tuple[str | Dict[str, Any], int]:
    """Cloud Functions HTTP Entry Point for YouTube Shorts Automation."""
    logger.info(f"🚀 Request received: Method={request.method}, Path={request.path}")

    # 기본 상태 확인을 위한 GET 요청 처리
    if request.method == "GET":
        logger.info("Health check GET request received. Returning healthy status.")
        return "✅ YouTube Shorts Cloud Function is healthy!", 200

    # POST 요청만 허용
    if request.method != "POST":
        logger.warning(f"Unsupported method {request.method} received. Only POST allowed.")
        return "⚠️ Only POST method allowed", 405

    # 환경 변수 체크
    project_id = os.environ.get("GCP_PROJECT_ID")
    bucket_name = os.environ.get("GCP_BUCKET_NAME")

    if not project_id or not bucket_name:
        logger.error("❌ Environment variables GCP_PROJECT_ID or GCP_BUCKET_NAME are missing.")
        return "❌ Missing environment variables: GCP_PROJECT_ID or GCP_BUCKET_NAME", 500

    config = Config(project_id=project_id, bucket_name=bucket_name)

    # --- 수정 시작: 임시 파일 처리 개선 ---
    # with tempfile.TemporaryDirectory() as temp_dir: 를 사용하여 자동으로 임시 디렉토리 정리
    # Cloud Functions는 /tmp 디렉토리를 사용하도록 설계됨
    temp_dir = tempfile.gettempdir()
    logger.info(f"Using temporary directory: {temp_dir}")
    # --- 수정 끝: 임시 파일 처리 개선 ---

    try:
        # ⭐ 수익 최적화 및 무료 한도 고려:
        # 매일 다양한 주제를 생성하여 더 많은 잠재 시청자에게 도달
        niche_keywords = [
            "신기한 과학", "건강 상식", "꿀팁", "기술 트렌드", "역사적 사실",
            "재미있는 심리", "일상 생활 해킹", "동물 이야기", "여행 정보", "미스터리",
            "자기계발", "재테크", "심리학 팁", "흥미로운 잡학", "지구촌 소식" # 주제 다양화
        ]
        selected_niche = random.choice(niche_keywords)
        
        # ⭐ AI 모델 선택 최적화:
        # GCP 무료 한도를 최대한 활용하기 위해 Gemini를 우선 사용합니다.
        # GPT-4o는 사용량에 따라 비용이 발생할 수 있으므로, 초기에는 Gemini로 안정화 후 고려합니다.
        # "openai" 모델을 사용하려면 OpenAI API Key를 Secrets Manager에 설정해야 합니다.
        ai_model = "gemini" # 우선 Gemini로 고정하여 안정성 확보 권장
        # ai_model = random.choice(["openai", "gemini"]) # 두 모델 모두 사용하려면 각 API의 한도를 철저히 모니터링해야 합니다.

        logger.info(f"✨ Selected Niche: {selected_niche}, AI Model: {ai_model}")
        
        # AI 콘텐츠 생성
        logger.info(f"Calling AI Manager to generate content for niche: '{selected_niche}' using model: '{ai_model}'")
        ai_response = generate_niche_content(config, selected_niche, ai_model)
        content = ai_response.get("content", "").strip()
        title = ai_response.get("title", "").strip()

        if not content or not title or len(content) < 50 or len(title) < 10: # 최소 길이 및 품질 기준 강화
            logger.error(f"❌ AI content generation failed: Insufficient content or invalid format. Content length: {len(content)}, Title length: {len(title)}")
            return "❌ AI failed to generate valid content or title (insufficient length/quality).", 500
        
        logger.info(f"✅ AI content generated. Title: '{title}', Content (first 100 chars): '{content[:100]}...'")

        # TTS 오디오 생성
        audio_path = os.path.join(temp_dir, f"voice_{datetime.now().timestamp()}.mp3") # 고유한 파일명
        logger.info(f"Generating TTS audio to: {audio_path}")
        generate_tts_audio(config.get_elevenlabs_api_key(), content, config.elevenlabs_voice_id, audio_path)
        if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
            logger.error(f"❌ TTS audio file not created or is empty: {audio_path}")
            return "❌ Failed to generate TTS audio.", 500
        logger.info(f"✅ TTS audio file created: {audio_path} (Size: {os.path.getsize(audio_path)} bytes)")

        # 배경 영상 다운로드
        video_path = os.path.join(temp_dir, f"bg_video_{datetime.now().timestamp()}.mp4") # 고유한 파일명
        logger.info(f"Downloading background video for niche: '{selected_niche}' to: {video_path}")
        download_background_video(config.get_pexels_api_key(), selected_niche, video_path)
        if not os.path.exists(video_path) or os.path.getsize(video_path) == 0:
            logger.error(f"❌ Background video file not downloaded or is empty: {video_path}")
            return "❌ Failed to download background video.", 500
        logger.info(f"✅ Background video downloaded: {video_path} (Size: {os.path.getsize(video_path)} bytes)")

        # 동영상 생성 및 편집 (MoviePy 사용)
        base_video_output_path = os.path.join(temp_dir, f"base_video_{datetime.now().timestamp()}.mp4")
        final_video_output_path = os.path.join(temp_dir, f"final_short_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")

        logger.info(f"Creating base video: {base_video_output_path}")
        # create_short_video 함수는 원본 비디오 경로, 오디오 경로, 최종 출력 경로를 받아
        # 베이스 비디오 파일을 생성하고 그 파일 경로를 반환해야 합니다.
        base_video_result_path = create_short_video(video_path, audio_path, base_video_output_path)
        if not os.path.exists(base_video_result_path) or os.path.getsize(base_video_result_path) == 0:
            logger.error(f"❌ Base video creation failed or file is empty: {base_video_result_path}")
            return "❌ Failed to create base video.", 500
        logger.info(f"✅ Base video created: {base_video_result_path} (Size: {os.path.getsize(base_video_result_path)} bytes)")


        logger.info(f"Editing final video: {final_video_output_path}")
        # edit_video_for_shorts 함수는 베이스 비디오 파일 경로, 콘텐츠, 제목을 받아
        # 최종 편집된 비디오 파일을 생성하고 그 파일 경로를 반환해야 합니다.
        edited_video_result_path = edit_video_for_shorts(base_video_result_path, content, title)
        if not os.path.exists(edited_video_result_path) or os.path.getsize(edited_video_result_path) == 0:
            logger.error(f"❌ Final video editing failed or file is empty: {edited_video_result_path}")
            return "❌ Failed to edit final video.", 500
        logger.info(f"✅ Final video edited: {edited_video_result_path} (Size: {os.path.getsize(edited_video_result_path)} bytes)")

        # MoviePy 작업 후 파일이 다른 이름으로 저장될 수 있으므로, 명시적으로 최종 이름을 설정
        if edited_video_result_path != final_video_output_path:
            os.rename(edited_video_result_path, final_video_output_path)
            logger.info(f"Moved edited video to final path: {final_video_output_path}")

        # YouTube에 영상 업로드
        logger.info(f"Attempting to upload video to YouTube: {final_video_output_path}")
        response_data = upload_video(
            final_video_output_path,
            title,
            # 설명과 태그 더 풍부하게 (SEO 최적화)
            f"주제: {selected_niche}\n\n{content}\n\n#Shorts #AI #유튜브자동화 #{selected_niche.replace(' ', '')} #인사이트 #지식 #정보",
            tags=[t.strip() for t in title.split()[:5]] + [selected_niche.replace(' ', ''), "AI생성", "YouTubeShorts", "자동화", datetime.now().strftime("%Y")] + ["짧은영상"], # 태그 다양화
            category_id="22", # Entertainment (대부분의 Shorts에 적합) 또는 "25" (뉴스 및 정치)
            privacy_status="public", # 수익화를 위해 필수
            config_instance=config
        )
        video_id = response_data.get('id')
        if not video_id:
            logger.error("❌ YouTube upload successful, but no video ID returned.")
            return "❌ YouTube upload completed but video ID is missing.", 500

        logger.info(f"🎉 YouTube upload complete: Video ID = {video_id}")
        return jsonify({"status": "Success", "video_id": video_id, "message": f"YouTube Shorts uploaded successfully with ID: {video_id}"}), 200

    except Exception as e:
        import traceback
        logger.error(f"🔥 An error occurred during function execution: {e}", exc_info=True) # 상세 스택 트레이스 로깅
        return jsonify({"status": "Error", "message": f"An error occurred: {str(e)}", "trace": traceback.format_exc()}), 500
