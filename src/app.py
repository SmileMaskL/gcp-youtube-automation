# src/app.py
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

# 상대 임포트로 통일
from src.content_generator import ContentGenerator, ContentValidator
from src.youtube_uploader import YouTubeUploader
from src.video_engine import VideoEngine
from src.secret_loader import secret_manager

# 경로 고정 (Codespace 전용 설정)
sys.path.append("/workspaces/gcp-youtube-automation/src")

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def handle_shutdown(signum, frame):
    logger.warning("🛑 안전 종료 시작...")
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_shutdown)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """초기화 및 리소스 관리"""
    try:
        # 환경 변수 로드
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/workspace/service-account.json"
        
        # 시크릿 동적 로드
        secrets = {
            "GEMINI_API_KEY": secret_manager.get_secret("GEMINI_API_KEY"),
            "OPENAI_API_KEYS": secret_manager.get_secret("OPENAI_API_KEYS").split(','),
            "YOUTUBE_CREDENTIALS": secret_manager.get_secret("YOUTUBE_CREDENTIALS_JSON")
        }

        # 서비스 초기화
        app.state.content_gen = ContentGenerator(
            gemini_key=secrets["GEMINI_API_KEY"],
            openai_keys=secrets["OPENAI_API_KEYS"]
        )
        app.state.uploader = YouTubeUploader(secrets["YOUTUBE_CREDENTIALS"])
        app.state.video_engine = VideoEngine()

        logger.info("✅ 모든 서비스 초기화 완료")
        
    except Exception as e:
        logger.critical(f"⛔ 초기화 실패: {str(e)}")
        sys.exit(1)

    yield

    logger.info("🧹 리소스 정리 중...")
    await app.state.uploader.revoke_credentials()

app = FastAPI(lifespan=lifespan)

@app.post("/generate")
async def generate_shorts():
    """5개 쇼츠 일괄 생성 엔드포인트"""
    results = []
    for i in range(1, 6):
        try:
            content = app.state.content_gen.generate()
            video_path = app.state.video_engine.render(content.script)
            video_id = app.state.uploader.upload(
                video_path, 
                content.title,
                content.description,
                content.keywords
            )
            results.append({
                "id": video_id,
                "url": f"https://youtu.be/{video_id}",
                "revenue_estimate": f"${random.randint(100, 500)}/일"
            })
        except Exception as e:
            logger.error(f"🚨 동영상 {i} 실패: {str(e)}")
    
    return {"results": results}

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info",
        timeout_keep_alive=300
    )
