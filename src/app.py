import os
import logging
<<<<<<< HEAD
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

# 로그 디렉토리 존재 확인
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
=======
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse

from youtube_uploader import YouTubeUploader # 'src.' 제거됨
from video_engine import VideoEngine
from secret_loader import secret_manager # 'src.' 제거됨
from config import settings # 이제 config.py에서 'settings' 객체를 찾을 수 있습니다.

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(
    title="YouTube 자동화 서비스",
    description="AI 쇼츠 비디오를 처리하고 YouTube에 업로드하는 API 서비스입니다.",
    version="1.0.0"
)

# YouTubeUploader 인스턴스를 전역 변수로 선언하되, 초기화는 startup 이벤트에서 진행
youtube_uploader: YouTubeUploader = None
video_engine = VideoEngine()

@app.on_event("startup")
async def startup_event():
    """
    FastAPI 애플리케이션 시작 시 실행되는 이벤트 핸들러입니다.
    여기서 YouTubeUploader를 초기화하여 앱 시작 오류를 방지합니다.
    """
    global youtube_uploader
    logging.info("애플리케이션 시작 이벤트: YouTubeUploader 초기화 시도...")

    try:
        # Secret Manager에서 YouTube API 자격 증명 로드
        # Secret Manager에 저장된 시크릿 ID를 여기에 명시해야 합니다.
        # 예: youtube-client-id, youtube-client-secret, youtube-refresh-token
        # --- 다음 줄들이 수정되었습니다 (대소문자 변경) ---
        client_id = os.getenv("YOUTUBE_CLIENT_ID")
        client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
        refresh_token =  os.getenv("YOUTUBE_REFRESH_TOKEN")
        # --- 수정 끝 ---

        if not all([client_id, client_secret, refresh_token]):
            logging.error("Secret Manager에서 YouTube API 자격 증명을 로드하는 데 실패했습니다. 일부가 누락되었습니다.")
            raise ValueError("불완전한 YouTube API 자격 증명.")

        youtube_uploader = YouTubeUploader({
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token
        })
        logging.info("✅ YouTubeUploader 초기화 성공.")
    except Exception as e:
        logging.error(f"❌ YouTubeUploader 초기화 중 치명적인 오류 발생: {e}")
        # 초기화 실패 시 youtube_uploader는 None으로 유지됩니다.
        # 이 경우 /upload_short 엔드포인트에서 오류를 반환할 것입니다.

@app.get("/")
async def read_root():
    """
    서비스의 루트 엔드포인트. 서비스가 정상 작동 중임을 알립니다.
    """
    return {"message": "YouTube 자동화 서비스가 실행 중입니다!"}

@app.get("/health")
async def health_check():
    """
    서비스의 상태를 확인하는 헬스 체크 엔드포인트.
    """
    # YouTubeUploader가 성공적으로 초기화되었는지도 헬스 체크에 포함
    uploader_status = "초기화됨" if youtube_uploader else "초기화 실패 또는 대기 중"
    return {"status": "ok", "message": "서비스가 정상적으로 작동하고 있습니다.", "youtube_uploader_status": uploader_status}

@app.post("/upload_short")
async def upload_short_video(
    video_file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(...),
    keywords: str = Form(None) # 콤마로 구분된 문자열로 받음
):
    """
    AI 쇼츠 비디오를 처리하고 YouTube에 업로드합니다.
    - `video_file`: 업로드할 비디오 파일 (mp4, mov 등)
    - `title`: YouTube 비디오 제목
    - `description`: YouTube 비디오 설명
    - `keywords`: 비디오 태그 (콤마로 구분된 문자열, 예: "AI, Shorts, Automation")
    """
    # YouTubeUploader가 성공적으로 초기화되었는지 확인
    if not youtube_uploader:
        logging.error("YouTube 업로드 서비스가 아직 초기화되지 않았거나 오류가 발생했습니다.")
        raise HTTPException(status_code=503, detail="YouTube 업로드 서비스가 준비되지 않았습니다. 잠시 후 다시 시도하거나 서버 로그를 확인하세요.")

    # 1. 비디오 파일 임시 저장
    # /tmp 디렉토리는 컨테이너 내에서 임시 파일을 저장하기에 적합합니다.
    input_video_path = f"/tmp/{video_file.filename}"
    try:
        # 비동기적으로 파일 내용을 읽고 저장합니다.
        with open(input_video_path, "wb") as buffer:
            buffer.write(await video_file.read())
        logging.info(f"수신된 비디오 파일 임시 저장: {input_video_path}")
    except Exception as e:
        logging.error(f"비디오 파일 저장 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=f"비디오 파일 저장 실패: {e}. 관리자에게 문의하세요.")

    # 2. 비디오 처리 (예: 텍스트 오버레이, 편집, 효과 추가 등)
    # VideoEngine을 사용하여 실제 비디오 처리 로직을 수행합니다.
    processed_video_path = f"/tmp/processed_{video_file.filename}"
    try:
        processing_success = video_engine.process_video(
            input_video_path=input_video_path,
            output_video_path=processed_video_path,
            text_overlay=f"자동 생성 쇼츠: {title}"
        )

        if not processing_success:
            logging.error("비디오 처리 엔진에서 오류가 발생했습니다.")
            raise HTTPException(status_code=500, detail="비디오 처리 중 오류가 발생했습니다. 비디오 엔진 로그를 확인하세요.")
        logging.info(f"비디오 처리 완료: {processed_video_path}")
    except Exception as e:
        logging.error(f"비디오 처리 중 예외 발생: {e}")
        raise HTTPException(status_code=500, detail=f"비디오 처리 중 예상치 못한 오류 발생: {e}")
    finally:
        # 원본 입력 파일은 처리 후 바로 삭제합니다.
        if os.path.exists(input_video_path):
            os.remove(input_video_path)
            logging.info(f"원본 비디오 파일 삭제: {input_video_path}")

    # 3. YouTube에 업로드
    try:
        # 콤마로 구분된 키워드 문자열을 리스트로 변환합니다.
        parsed_keywords = [kw.strip() for kw in keywords.split(',')] if keywords else None
        
        video_id = youtube_uploader.upload(
            video_path=processed_video_path,
            title=title,
            description=description,
            keywords=parsed_keywords
        )
        logging.info(f"YouTube 업로드 성공. 비디오 ID: {video_id}")
        return JSONResponse(
            status_code=200,
            content={"message": "비디오가 성공적으로 업로드되었습니다.", "video_id": video_id, "youtube_url": f"https://www.youtube.com/watch?v={video_id}"}
        )
    except Exception as e:
        logging.error(f"YouTube 업로드 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=f"YouTube 업로드 실패: {e}. API 자격 증명 또는 네트워크 상태를 확인하세요.")
    finally:
        # 처리된 비디오 파일도 업로드 후 삭제합니다.
        if os.path.exists(processed_video_path):
            os.remove(processed_video_path)
            logging.info(f"처리된 비디오 파일 삭제: {processed_video_path}")
>>>>>>> 39084fc7b559941b38b6aa3e14ae067a1e397f39
