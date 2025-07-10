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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(
    title="YouTube 자동화 서비스",
    description="AI 쇼츠 비디오를 처리하고 YouTube에 업로드하는 API 서비스입니다.",
    version="1.0.0"
)

# 환경 변수에서 YouTube API 자격 증명 로드
# 실제 운영 환경에서는 더 안전한 방법(예: Google Secret Manager)을 사용해야 합니다.
CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID")
CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("YOUTUBE_REFRESH_TOKEN")

# YouTubeUploader 인스턴스 초기화
# 앱 시작 시 한 번만 초기화되도록 합니다.
youtube_uploader = None
try:
    if CLIENT_ID and CLIENT_SECRET and REFRESH_TOKEN:
        youtube_uploader = YouTubeUploader({
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": REFRESH_TOKEN
        })
        logging.info("YouTubeUploader 초기화 시도 완료.")
    else:
        logging.warning("YouTube API 자격 증명 환경 변수가 설정되지 않았습니다. YouTube 업로드 기능이 비활성화됩니다.")
except Exception as e:
    logging.error(f"YouTubeUploader 초기화 중 오류 발생: {e}")
    youtube_uploader = None # 오류 발생 시 None으로 설정하여 업로드 기능 비활성화

video_engine = VideoEngine()

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
    return {"status": "ok", "message": "서비스가 정상적으로 작동하고 있습니다."}

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
    if not youtube_uploader:
        logging.error("YouTube 업로드 서비스가 초기화되지 않아 요청을 처리할 수 없습니다.")
        raise HTTPException(status_code=503, detail="YouTube 업로드 서비스가 초기화되지 않았습니다. API 자격 증명을 확인하세요.")

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
    # 이 예시에서는 단순히 입력 파일을 출력 파일로 복사하는 모의 처리입니다.
    processed_video_path = f"/tmp/processed_{video_file.filename}"
    try:
        # 실제 비디오 처리 로직은 VideoEngine 내부에 구현됩니다.
        # 여기서는 예시로 title을 텍스트 오버레이로 사용합니다.
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
