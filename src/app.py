# src/app.py

import logging
import os # 환경 변수를 읽기 위해 추가
from fastapi import FastAPI, Request, HTTPException
import uvicorn

# 로거 설정: Cloud Run의 로깅 시스템과 통합됩니다.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info("Application starting...")

try:
    app = FastAPI()
    logger.info("FastAPI app instance created successfully.")
except Exception as e:
    logger.error(f"Error creating FastAPI app instance: {e}")
    raise # 오류 발생 시 즉시 종료하여 로그 확인

@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행되는 로직."""
    logger.info("FastAPI application startup event triggered.")
    # 필요한 환경 변수 로드 및 검증 (예시)
    gemini_key = os.getenv("GEMINI_API_KEY")
    elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")

    if not gemini_key:
        logger.error("GEMINI_API_KEY environment variable is not set.")
        # 실제 운영 환경에서는 앱 시작을 막거나 적절히 처리해야 합니다.
    else:
        logger.info("GEMINI_API_KEY is set.")

    if not elevenlabs_key:
        logger.error("ELEVENLABS_API_KEY environment variable is not set.")
    else:
        logger.info("ELEVENLABS_API_KEY is set.")

    logger.info("Application startup complete.")


@app.post("/")
async def root(request: Request):
    """루트 엔드포인트: Pub/Sub 트리거를 처리합니다."""
    logger.info("Received request on root endpoint.")
    try:
        data = await request.json()
        logger.info(f"Request data: {data}")
        # Pub/Sub 메시지 형식에 따라 필요한 로직을 추가합니다.
        # 예: {"message": {"data": "base64encoded_payload", "attributes": {}}}
        # 실제 페이로드를 디코딩하고 처리하는 로직 필요
        return {"message": "Root endpoint received data", "data": data}
    except Exception as e:
        logger.error(f"Error processing root request: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@app.post("/generate")
async def generate_content(request: Request):
    """AI 콘텐츠 생성 엔드포인트."""
    logger.info("Received request on /generate endpoint.")
    try:
        data = await request.json()
        logger.info(f"Generate content data: {data}")
        # 여기에 AI 콘텐츠 생성 로직 삽입
        # 예: Gemini API 호출, Pexels API 호출 등
        return {"message": "Content generation initiated", "data": data}
    except Exception as e:
        logger.error(f"Error generating content: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@app.post("/upload")
async def upload_video(request: Request):
    """유튜브 업로드 엔드포인트."""
    logger.info("Received request on /upload endpoint.")
    try:
        data = await request.json()
        logger.info(f"Upload video data: {data}")
        # 여기에 유튜브 업로드 로직 삽입
        return {"message": "Video upload initiated", "data": data}
    except Exception as e:
        logger.error(f"Error uploading video: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


if __name__ == "__main__":
    # 로컬 개발 환경에서만 uvicorn으로 직접 실행
    # Cloud Run에서는 Gunicorn이 이 파일을 로드합니다.
    logger.info("Running uvicorn locally.")
    uvicorn.run("app:app", host="0.0.0.0", port=8080, log_level="info")
