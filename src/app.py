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

# 사용자 정의 모듈 임포트
from content_generator import ContentGenerator
from youtube_uploader import YouTubeUploader
from video_engine import VideoEngine
from secret_loader import secret_manager  # 수정된 부분

# 로그 디렉토리 설정
log_dir = "/var/log"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 로깅 구성
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
    logger.warning("🛑 종료 신호 수신. 안전한 종료 절차 시작...")
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_shutdown)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 AI 쇼츠 팩토리 초기화 중...")
    
    try:
        # GCP 시크릿 매니저에서 동적 로드 (수정된 부분)
        gemini_key = secret_manager.get_secret("GEMINI_API_KEY")
        openai_keys = secret_manager.get_secret("OPENAI_API_KEYS")
        yt_creds = secret_manager.get_secret("YOUTUBE_CREDENTIALS_JSON")
        
        # 서비스 인스턴스 초기화
        app.state.content_gen = ContentGenerator(
            gemini_key=gemini_key,
            openai_keys=openai_keys.split(',')
        )
        app.state.uploader = YouTubeUploader(
            credentials_json=yt_creds
        )
        app.state.video_engine = VideoEngine(
            ffmpeg_path="/usr/bin/ffmpeg",
            exiftool_path="/usr/local/bin/exiftool"
        )
        
    except Exception as e:
        logger.critical(f"⛔️ 시스템 초기화 실패: {str(e)}")
        sys.exit(1)
    
    yield
    
    logger.info("🧹 리소스 정리 중...")
    await app.state.uploader.revoke_credentials()

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health_check():
    """서버 상태 확인 엔드포인트"""
    return {
        "status": "ok",
        "timestamp": time.time(),
        "environment": os.getenv("ENV", "development")
    }

@app.post("/generate")
async def generate_shorts():
    """5개의 쇼츠 동영상 생성 및 업로드"""
    try:
        results = []
        for i in range(5):
            logger.info(f"🎥 {i+1}/5번째 동영상 처리 중")
            
            # 콘텐츠 생성
            content = app.state.content_gen.generate()
            if not content.validate():
                raise HTTPException(
                    status_code=500,
                    detail="생성된 콘텐츠 유효성 검사 실패"
                )
            
            # 비디오 렌더링
            video_path = app.state.video_engine.render(
                script=content.script,
                assets=content.assets
            )
            
            # YouTube 업로드
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
        logger.error(f"💥 치명적 오류: {str(e)}")
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
