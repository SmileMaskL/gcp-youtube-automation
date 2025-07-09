import logging
import os
import json
import traceback # Import traceback for detailed error logging
from fastapi import FastAPI, Request, HTTPException
import uvicorn
from content_generator import generate_content_and_script # content_generator.py에서 import
from youtube_uploader import upload_video_to_youtube # youtube_uploader.py에서 import
from openai_utils import get_next_openai_key # openai_utils.py에서 import

# 로깅 설정: Cloud Run/Logging에서 보기 좋게 시간, 레벨, 메시지 포맷 지정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# FastAPI 애플리케이션 인스턴스 생성
# 이 'app' 변수가 Dockerfile의 CMD에서 'app:app'으로 참조됩니다.
app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """
    FastAPI 애플리케이션 시작 시 실행되는 이벤트.
    필수 환경 변수를 검증하고, 애플리케이션 초기화 작업을 수행합니다.
    """
    logger.info("FastAPI application startup event triggered.")
    
    # Cloud Run은 PORT 환경 변수를 자동으로 설정합니다.
    # 이를 확인하여 애플리케이션이 올바른 포트에서 시작할 준비가 되었는지 로깅합니다.
    port = os.getenv("PORT", "8080") # 기본값은 8080
    logger.info(f"Application expects to listen on port: {port}")

    # 필수 환경 변수 검증
    # 실제 사용될 모든 API 키 및 인증 정보가 환경 변수로 설정되어 있는지 확인
    required_envs = [
        "GEMINI_API_KEY", 
        "NEWSAPI_API_KEY", 
        "OPENAI_API_KEYS",
        "YOUTUBE_CLIENT_ID", 
        "YOUTUBE_CLIENT_SECRET", 
        "YOUTUBE_REFRESH_TOKEN",
        # 추가적으로 필요한 환경 변수가 있다면 여기에 명시
        # 예: ELEVENLABS_API_KEY 등
    ]
    for env in required_envs:
        if not os.getenv(env):
            logger.error(f"Environment variable '{env}' is not set. This is a critical error.")
            # 환경 변수 누락은 애플리케이션 시작 실패의 주요 원인이므로, RuntimeError를 발생시켜 배포 실패를 명확히 합니다.
            raise RuntimeError(f"Missing required environment variable: {env}")
    logger.info("All required environment variables are set.")

@app.post("/")
async def create_and_upload_shorts(request: Request):
    """
    하루 5개 인기 검색어 기반 유튜브 Shorts 자동 생성 및 업로드 엔드포인트.
    이 엔드포인트는 Cloud Run에 의해 호출될 때 실행됩니다.
    """
    logger.info("Received request to create and upload 5 Shorts.")
    results = []
    
    try:
        # 환경 변수 로드 (startup_event에서 검증되었으므로 바로 사용)
        gemini_api_key = os.environ["GEMINI_API_KEY"]
        news_api_key = os.environ["NEWSAPI_API_KEY"]
        openai_api_keys_str = os.environ["OPENAI_API_KEYS"]
        openai_api_keys = openai_api_keys_str.split(",")

        client_id = os.environ["YOUTUBE_CLIENT_ID"]
        client_secret = os.environ["YOUTUBE_CLIENT_SECRET"]
        refresh_token = os.environ["YOUTUBE_REFRESH_TOKEN"]

        # 실제 OpenAI 키가 제대로 분리되는지 확인 (디버깅 목적)
        logger.info(f"Detected {len(openai_api_keys)} OpenAI API keys.")
        if not openai_api_keys or not all(key.startswith("sk-") for key in openai_api_keys):
            logger.error("OPENAI_API_KEYS are not correctly configured or empty.")
            raise ValueError("OPENAI_API_KEYS are not properly set.")

        # 병렬 처리를 고려할 수 있지만, 여기서는 순차적으로 5회 실행
        for i in range(5):
            logger.info(f"🔁 Generating video {i+1}/5")
            
            # OpenAI 키 로테이션 적용
            selected_openai_key = get_next_openai_key(openai_api_keys)
            logger.info(f"Using OpenAI key (first 8 chars): {selected_openai_key[:8]}...") # 보안을 위해 키의 일부만 로깅

            # --- 이 부분에서 오류 발생 (app.py:92) ---
            # content_generator.py의 generate_content_and_script 함수가 호출됩니다.
            # 이 함수 내부에서 문제가 발생하고 있을 가능성이 매우 높습니다.
            try:
                # content = generate_content_and_script(gemini_api_key, news_api_key, openai_api_keys) # 주석처리된 이전 코드
                # 현재 로직대로 selected_openai_key 단일 값을 전달합니다.
                logger.info("Calling generate_content_and_script with provided API keys.")
                content = generate_content_and_script(gemini_api_key, news_api_key, selected_openai_key)
                logger.info(f"Content generated for video {i+1}: Title='{content.get('title', 'N/A')}'")
            except Exception as e:
                # generate_content_and_script 함수 내에서 발생하는 모든 예외를 여기서 캐치하여 상세 로깅합니다.
                logger.error(f"Error in generate_content_and_script for video {i+1}: {e}")
                logger.error(traceback.format_exc()) # 전체 traceback 로깅
                raise HTTPException(status_code=500, detail=f"Content generation failed for video {i+1}.")

            # 대본 저장
            # /tmp는 Cloud Run 컨테이너에서 유일하게 쓰기 가능한 임시 디렉토리입니다.
            script_path = f"/tmp/script_{i+1}.txt"
            try:
                with open(script_path, "w", encoding="utf-8") as f:
                    f.write(content["script"])
                logger.info(f"Script saved to {script_path}")
            except Exception as e:
                logger.error(f"Error saving script to {script_path}: {e}")
                logger.error(traceback.format_exc())
                raise HTTPException(status_code=500, detail="Failed to save script file.")

            # --- 🎬 실제 영상 생성 로직 필요 ---
            # 현재는 더미 파일 생성: 이 부분이 실제 동작하려면 moviepy 등을 이용한 영상 생성 로직이 필요합니다.
            # 이 "FAKE_VIDEO" 부분에서 오류가 발생할 가능성이 가장 높습니다.
            # MoviePy, ffmpeg-python 등을 사용하여 content['script']와 content['images'] 등을 기반으로 영상을 만드세요.
            video_path = f"/tmp/video_{i+1}.mp4"
            
            # 실제 영상 생성 함수 호출 (예시)
            # from video_generator import generate_video_from_script
            # generate_video_from_script(script_path, content["images"], video_path)
            
            # 더미 파일 생성 (임시) - 실제 배포 시에는 반드시 이 부분을 실제 로직으로 교체해야 합니다.
            try:
                # 간단한 빈 파일 생성 또는 작은 더미 데이터 쓰기
                with open(video_path, "wb") as f:
                    f.write(b"This is a placeholder video file. REPLACE THIS!")
                logger.warning(f"Placeholder video created at {video_path}. REPLACE THIS WITH ACTUAL VIDEO GENERATION LOGIC!")
            except Exception as e:
                logger.error(f"Error creating placeholder video: {e}")
                logger.error(traceback.format_exc())
                raise HTTPException(status_code=500, detail="Failed to create placeholder video.")
            # --- 🎬 영상 생성 로직 끝 ---

            # 유튜브 업로드
            logger.info(f"Attempting to upload video {i+1} to YouTube...")
            try:
                upload_video_to_youtube(
                    client_id,
                    client_secret,
                    refresh_token,
                    video_path,
                    content["title"],
                    content["description"]
                )
                results.append({"title": content["title"], "status": "uploaded"})
                logger.info(f"Video '{content['title']}' uploaded successfully.")
            except Exception as e:
                logger.error(f"Error uploading video {i+1} to YouTube: {e}")
                logger.error(traceback.format_exc())
                raise HTTPException(status_code=500, detail=f"YouTube upload failed for video {i+1}.")

            # 임시 파일 정리 (선택 사항, 하지만 Cloud Run의 /tmp 공간 관리에 좋음)
            try:
                os.remove(script_path)
                os.remove(video_path)
                logger.info(f"Cleaned up temporary files: {script_path}, {video_path}")
            except OSError as e:
                logger.warning(f"Error cleaning up temporary files: {e}")

        return {"status": "success", "uploaded_videos": results}

    except ValueError as ve:
        logger.error(f"Configuration error: {ve}")
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Configuration error: {str(ve)}")
    except FileNotFoundError as fnfe:
        logger.error(f"File not found error: {fnfe}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Required file not found: {str(fnfe)}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during Shorts generation/upload: {e}")
        # 전체 트레이스백을 로그에 기록하여 상세 오류 확인
        traceback.print_exc() 
        # 사용자에게는 일반적인 오류 메시지를 반환
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {str(e)}")


if __name__ == "__main__":
    # 로컬에서 실행할 때만 uvicorn을 직접 실행합니다.
    # Cloud Run 환경에서는 Gunicorn이 uvicorn 워커를 관리합니다.
    # 이 부분은 로컬 개발 및 테스트를 위한 것이며, Cloud Run 배포와 직접적인 관련은 적습니다.
    # 하지만 로컬 테스트 시에도 --host 0.0.0.0 과 PORT를 사용하는 것이 좋습니다.
    port = int(os.getenv("PORT", 8080)) # PORT 환경 변수가 있으면 사용, 없으면 8080
    logger.info(f"Starting uvicorn server for local development on port {port}...")
    uvicorn.run("app:app", host="0.0.0.0", port=port, log_level="info")
