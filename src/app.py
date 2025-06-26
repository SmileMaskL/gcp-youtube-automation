import os
import logging
from flask import Flask, request, jsonify
from youtube_uploader import YoutubeUploader
from content_generator import ContentGenerator
from tts_generator import TTSGenerator
from video_creator import VideoCreator
from utils import setup_logging, clean_up_old_files

# 로깅 설정 (기존 setup_logging 함수 사용)
setup_logging()
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 환경 변수 설정
# Cloud Run 환경에서 PORT 환경 변수는 자동으로 주입됩니다.
# 로컬 테스트를 위해 기본값 8080을 설정합니다.
PORT = int(os.environ.get("PORT", 8080))

# ⚠️ 중요: 환경 변수는 Cloud Run 배포 시 Secret Manager를 통해 안전하게 주입되어야 합니다.
# 여기서는 예시를 위해 직접 환경 변수를 읽는 것처럼 보이지만, 실제 배포는 Secret Manager를 사용합니다.
YOUTUBE_CLIENT_ID = os.environ.get("YOUTUBE_CLIENT_ID")
YOUTUBE_CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET")
YOUTUBE_REFRESH_TOKEN = os.environ.get("YOUTUBE_REFRESH_TOKEN")
NEWSAPI_API_KEY = os.environ.get("NEWSAPI_API_KEY")
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
OPENAI_API_KEYS = os.environ.get("OPENAI_API_KEYS") # 쉼표로 구분된 문자열로 가정

# Flask 라우트 정의
@app.route("/", methods=["GET"])
def health_check():
    """Cloud Run 헬스 체크를 위한 간단한 응답."""
    return "OK", 200

@app.route("/upload-youtube-shorts", methods=["POST"])
def trigger_youtube_upload():
    """
    YouTube Shorts 업로드 프로세스를 시작하는 엔드포인트.
    이벤트 기반 트리거 역할을 합니다 (예: Cloud Scheduler).
    """
    logger.info("YouTube Shorts 업로드 프로세스 시작 요청 수신.")

    try:
        # 환경 변수 유효성 검사 (간단화)
        if not all([YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN,
                    NEWSAPI_API_KEY, PEXELS_API_KEY, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID,
                    GEMINI_API_KEY, OPENAI_API_KEYS]):
            logger.error("필수 환경 변수가 설정되지 않았습니다.")
            return jsonify({"status": "error", "message": "Missing environment variables."}), 500

        # AI 모델 초기화 (GPT-4o 또는 Gemini 선택 및 활용)
        # 이 부분은 환경 변수나 설정 파일에 따라 동적으로 선택될 수 있습니다.
        # 여기서는 예시로 두 AI 모두를 사용하는 로직을 가정합니다.
        ai_model_for_content = "gemini" # 또는 "gpt-4o"
        ai_model_for_summary = "openai" # 또는 "gemini"

        content_generator = ContentGenerator(
            news_api_key=NEWSAPI_API_KEY,
            pexels_api_key=PEXELS_API_KEY,
            gemini_api_key=GEMINI_API_KEY,
            openai_api_keys=OPENAI_API_KEYS.split(',') if OPENAI_API_KEYS else []
        )
        tts_generator = TTSGenerator(
            elevenlabs_api_key=ELEVENLABS_API_KEY,
            elevenlabs_voice_id=ELEVENLABS_VOICE_ID
        )
        video_creator = VideoCreator()
        youtube_uploader = YoutubeUploader(
            client_id=YOUTUBE_CLIENT_ID,
            client_secret=YOUTUBE_CLIENT_SECRET,
            refresh_token=YOUTUBE_REFRESH_TOKEN
        )

        logger.info("컨텐츠 생성 시작...")
        title, script, tags, categories, video_path, thumbnail_path = content_generator.generate_and_curate_content(
            ai_model_for_content=ai_model_for_content,
            ai_model_for_summary=ai_model_for_summary
        )

        # 수익 창출을 위한 내용 보강 (예시)
        # - 트렌드 API를 통해 요즘 인기 있는 키워드를 추가하여 조회수 극대화
        # - 시청자들이 댓글을 달도록 유도하는 질문을 스크립트에 추가 (comment_poster와 연계)
        # - 특정 시간대에 업로드하여 잠재 시청자 도달률 높이기 (daily_upload.yaml과 연계)

        if not video_path:
            logger.error("비디오 생성에 실패했습니다.")
            return jsonify({"status": "error", "message": "Failed to create video."}), 500

        logger.info(f"YouTube 업로드 시작: 제목='{title}'")
        video_id = youtube_uploader.upload_video(video_path, title, script, tags, categories)

        if video_id:
            logger.info(f"YouTube Shorts 업로드 성공! 비디오 ID: {video_id}")
            # 업로드 후 불필요한 파일 정리
            clean_up_old_files()
            return jsonify({"status": "success", "video_id": video_id}), 200
        else:
            logger.error("YouTube Shorts 업로드에 실패했습니다.")
            return jsonify({"status": "error", "message": "YouTube Shorts upload failed."}), 500

    except Exception as e:
        logger.exception(f"업로드 프로세스 중 오류 발생: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    # Cloud Run은 환경 변수 PORT를 사용합니다.
    # 로컬에서 실행할 경우 'python src/app.py'로 실행하면 8080 포트에서 실행됩니다.
    logger.info(f"애플리케이션이 포트 {PORT}에서 실행됩니다.")
    app.run(debug=True, host="0.0.0.0", port=PORT)
