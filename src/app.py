import logging
import os
import json
import traceback # Import traceback for detailed error logging
from fastapi import FastAPI, Request, HTTPException
import uvicorn
from content_generator import generate_content_and_script
from youtube_uploader import upload_video_to_youtube
from openai_utils import get_next_openai_key

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    logger.info("FastAPI application startup event triggered.")
    # 필수 환경 변수 검증
    required_envs = ["GEMINI_API_KEY", "NEWSAPI_API_KEY", "OPENAI_API_KEYS",
                     "YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN"]
    for env in required_envs:
        if not os.getenv(env):
            logger.error(f"{env} is not set. Exiting.")
            raise RuntimeError(f"{env} is required")

@app.post("/")
async def create_and_upload_shorts(request: Request):
    """
    하루 5개 인기 검색어 기반 유튜브 Shorts 자동 생성 및 업로드
    """
    logger.info("Received request to create and upload 5 Shorts.")
    results = []
    try:
        gemini_api_key = os.environ["GEMINI_API_KEY"]
        news_api_key = os.environ["NEWSAPI_API_KEY"]
        openai_api_keys = os.environ["OPENAI_API_KEYS"].split(",")

        client_id = os.environ["YOUTUBE_CLIENT_ID"]
        client_secret = os.environ["YOUTUBE_CLIENT_SECRET"]
        refresh_token = os.environ["YOUTUBE_REFRESH_TOKEN"]

        for i in range(5):
            logger.info(f"🔁 Generating video {i+1}/5")
            # OpenAI 키 로테이션 적용
            selected_openai_key = get_next_openai_key(openai_api_keys)

            # 콘텐츠 생성
            # Note: The original code passes openai_api_keys to generate_content_and_script
            # but then uses selected_openai_key for other parts.
            # If generate_content_and_script needs a single key, you might pass selected_openai_key.
            # For now, keeping it as original: openai_api_keys
            content = generate_content_and_script(gemini_api_key, news_api_key, openai_api_keys)

            # 대본 저장
            script_path = f"/tmp/script_{i+1}.txt"
            with open(script_path, "w") as f:
                f.write(content["script"])
            logger.info(f"Script saved to {script_path}")

            # 🎬 영상 생성 로직 (예시: TTS + MoviePy)
            # 실제 생성 함수는 별도 구현 필요
            video_path = f"/tmp/video_{i+1}.mp4"
            with open(video_path, "w") as f:
                f.write("FAKE_VIDEO") # placeholder
            logger.info(f"Placeholder video created at {video_path}")


            # 유튜브 업로드
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

        return {"status": "success", "uploaded_videos": results}

    except Exception as e:
        logger.error(f"An error occurred during Shorts generation/upload: {e}")
        traceback.print_exc() # Print full traceback for debugging
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {str(e)}")


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8080, log_level="info")
