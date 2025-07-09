import os
import logging
import signal
import sys
import time
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

# 모듈 임포트 (이 파일들과 동일한 디렉토리에 있어야 합니다.)
from content_generator import ContentGenerator
from youtube_uploader import YouTubeUploader
from video_engine import VideoEngine

# 로깅 설정
# Cloud Run에서는 로그를 stdout/stderr로 출력하는 것이 권장됩니다.
# 파일 핸들러는 제거하고 StreamHandler만 사용합니다.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout) # 모든 로그를 표준 출력으로 보냅니다.
    ]
)
logger = logging.getLogger(__name__)

# Graceful Shutdown 핸들러
def handle_shutdown(signum, frame):
    logger.warning("🛑 Received shutdown signal. Initiating graceful termination...")
    sys.exit(0) # 정상 종료

signal.signal(signal.SIGTERM, handle_shutdown)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Initializing AI Shorts Factory...")

    required_envs = {
        "GEMINI_API_KEY": "Google Gemini API Key",
        "OPENAI_API_KEYS": "OpenAI API Keys (comma-separated)",
        "YOUTUBE_CREDENTIALS_JSON": "Base64 encoded YouTube OAuth2 credentials"
    }
    missing = [k for k in required_envs if not os.getenv(k)]
    if missing:
        error_msg = f"❌ CRITICAL ERROR: Missing required environment variables: {', '.join(missing)}. Please set these variables during deployment."
        logger.critical(error_msg)
        # 환경 변수 누락 시 애플리케이션 시작을 중단하고 종료합니다.
        # Cloud Run은 이 종료를 컨테이너 시작 실패로 간주합니다.
        sys.exit(1)

    try:
        # 싱글톤 서비스 초기화
        app.state.content_gen = ContentGenerator(
            gemini_key=os.getenv("GEMINI_API_KEY"),
            openai_keys=os.getenv("OPENAI_API_KEYS").split(',')
        )
        app.state.uploader = YouTubeUploader(
            credentials_json=os.getenv("YOUTUBE_CREDENTIALS_JSON")
        )
        app.state.video_engine = VideoEngine(
            ffmpeg_path="/usr/bin/ffmpeg",
            exiftool_path="/usr/local/bin/exiftool"
        )
        logger.info("✅ AI Shorts Factory initialized successfully.")
    except Exception as e:
        logger.critical(f"💥 Failed to initialize AI Shorts Factory: {e}")
        logger.critical(traceback.format_exc())
        sys.exit(1) # 초기화 실패 시 종료

    yield

    logger.info("🧹 Cleaning up resources...")
    # uploader가 초기화되지 않았을 수 있으므로 확인
    if hasattr(app.state, 'uploader') and app.state.uploader:
        app.state.uploader.revoke_credentials()
    logger.info("✅ Resources cleaned up.")

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health_check():
    logger.info("💖 Health check requested.")
    return {"status": "ok", "timestamp": time.time()}

@app.post("/generate")
async def generate_shorts():
    try:
        results = []
        # 실제 운영 환경에서는 이 루프를 외부에서 제어하거나,
        # 단일 요청에 대한 응답으로 처리하는 것이 좋습니다.
        # Cloud Run의 요청 제한 시간(기본 5분, 최대 60분)을 고려해야 합니다.
        for i in range(1): # 테스트를 위해 1회만 실행하도록 변경
            logger.info(f"🎥 Processing video {i+1}/1")

            content = app.state.content_gen.generate()
            if not content.validate():
                logger.error("🚫 Invalid content generated.")
                raise HTTPException(status_code=500, detail="Invalid content generated")

            video_path = app.state.video_engine.render(
                script=content.script,
                assets=content.assets
            )
            logger.info(f"🎬 Video rendered: {video_path}")

            video_id = app.state.uploader.upload(
                file_path=video_path,
                title=content.title,
                description=content.description,
                tags=content.tags
            )
            logger.info(f"⬆️ Video uploaded with ID: {video_id}")

            results.append({
                "video_id": video_id,
                "title": content.title,
                "url": f"https://youtu.be/{video_id}" # 이 URL 형식은 YouTube API에서 직접 제공하는 것이 아니므로 주의
            })

        return JSONResponse(
            content={"status": "success", "results": results},
            status_code=201
        )

    except Exception as e:
        logger.error(f"💥 Critical failure during generation: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            content={"status": "error", "detail": str(e)},
            status_code=500
        )

if __name__ == "__main__":
    # uvicorn.run은 main 함수에서만 사용됩니다.
    # Cloud Run은 CMD 명령을 통해 uvicorn을 직접 실행하므로,
    # 이 __name__ == "__main__" 블록은 Cloud Run 환경에서는 실행되지 않습니다.
    # 하지만 로컬 테스트를 위해 유지하는 것이 좋습니다.
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
        log_config=None, # FastAPI의 기본 로깅을 사용하고, 위에서 설정한 로거를 따릅니다.
        timeout_keep_alive=300,
        access_log=False # 액세스 로그는 Cloud Run에서 자동으로 처리되므로 비활성화
    )
