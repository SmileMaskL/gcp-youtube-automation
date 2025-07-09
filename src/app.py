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

# 모듈 임포트
from content_generator import ContentGenerator
from youtube_uploader import YouTubeUploader
from video_engine import VideoEngine

# 로그 디렉토리 존재 확인 및 생성
log_dir = "/var/log"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/var/log/app.log')
    ]
)
logger = logging.getLogger(__name__)

# Graceful Shutdown 핸들러
def handle_shutdown(signum, frame):
    logger.warning("🛑 Received shutdown signal. Initiating graceful termination...")
    sys.exit(0)

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
        error_msg = f"❌ Missing critical env vars: {', '.join(missing)}"
        logger.critical(error_msg)
        raise RuntimeError(error_msg)

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

    yield

    logger.info("🧹 Cleaning up resources...")
    app.state.uploader.revoke_credentials()

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": time.time()}

@app.post("/generate")
async def generate_shorts():
    try:
        results = []
        for i in range(5):
            logger.info(f"🎥 Processing video {i+1}/5")

            content = app.state.content_gen.generate()
            if not content.validate():
                raise HTTPException(status_code=500, detail="Invalid content generated")

            video_path = app.state.video_engine.render(
                script=content.script,
                assets=content.assets
            )

            video_id = app.state.uploader.upload(
                file_path=video_path,
                title=content.title,
                description=content.description,
                tags=content.tags
            )

            results.append({
                "video_id": video_id,
                "title": content.title,
                "url": f"https://youtu.be/{video_id}"
            })

        return JSONResponse(
            content={"status": "success", "results": results},
            status_code=201
        )

    except Exception as e:
        logger.error(f"💥 Critical failure: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            content={"status": "error", "detail": str(e)},
            status_code=500
        )

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
        log_config=None,
        timeout_keep_alive=300,
        access_log=False
    )
