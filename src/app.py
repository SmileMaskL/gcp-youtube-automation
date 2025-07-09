import logging
import os
import traceback
from fastapi import FastAPI, Request, HTTPException
import uvicorn

# 실전 import
from content_generator import generate_content_and_script
from youtube_uploader import upload_video_to_youtube
from openai_utils import get_next_openai_key
from video_generator import generate_video_from_script

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    logger.info("FastAPI startup triggered.")

    # 필수 환경변수 체크
    required_envs = [
        "GEMINI_API_KEY",
        "NEWSAPI_API_KEY",
        "OPENAI_API_KEYS",
        "YOUTUBE_CLIENT_ID",
        "YOUTUBE_CLIENT_SECRET",
        "YOUTUBE_REFRESH_TOKEN",
    ]
    missing_envs = [env for env in required_envs if not os.getenv(env)]
    if missing_envs:
        for env in missing_envs:
            logger.error(f"❌ Missing required env var: {env}")
        raise RuntimeError(f"Missing required env vars: {', '.join(missing_envs)}")
    logger.info("✅ All required env vars set.")

@app.post("/")
async def create_and_upload_shorts(request: Request):
    logger.info("POST / called: starting Shorts generation pipeline.")
    results = []

    try:
        gemini_api_key = os.environ["GEMINI_API_KEY"]
        news_api_key = os.environ["NEWSAPI_API_KEY"]
        openai_api_keys = os.environ["OPENAI_API_KEYS"].split(",")

        client_id = os.environ["YOUTUBE_CLIENT_ID"]
        client_secret = os.environ["YOUTUBE_CLIENT_SECRET"]
        refresh_token = os.environ["YOUTUBE_REFRESH_TOKEN"]

        valid_keys = [k for k in openai_api_keys if k.startswith("sk-")]
        if not valid_keys:
            raise ValueError("No valid OPENAI_API_KEYS provided.")
        logger.info(f"{len(valid_keys)} OpenAI keys loaded.")

        for i in range(5):
            logger.info(f"🎬 Generating video {i+1}/5")
            selected_key = get_next_openai_key(valid_keys)
            logger.info(f"Using OpenAI key: {selected_key[:8]}****")

            try:
                content = generate_content_and_script(gemini_api_key, news_api_key, selected_key)
                if not content or not content.get("script"):
                    raise ValueError("Content generation returned empty script.")
                logger.info(f"Generated content: {content.get('title', 'No Title')}")
            except Exception as e:
                logger.error(f"[Error] generate_content_and_script: {e}")
                logger.error(traceback.format_exc())
                raise HTTPException(status_code=500, detail=f"Content generation failed for video {i+1}: {e}")

            script_path = f"/tmp/script_{i+1}.txt"
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(content["script"])
            logger.info(f"Script saved: {script_path}")

            video_path = f"/tmp/video_{i+1}.mp4"
            try:
                generate_video_from_script(script_path, content.get("images", []), video_path)
                logger.info(f"Video generated at: {video_path}")
            except Exception as e:
                logger.error(f"Video generation error: {e}")
                logger.error(traceback.format_exc())
                raise HTTPException(status_code=500, detail=f"Video generation failed for video {i+1}: {e}")

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
                logger.info(f"✅ Uploaded video {i+1}: {content['title']}")
            except Exception as e:
                logger.error(f"Upload error: {e}")
                logger.error(traceback.format_exc())
                raise HTTPException(status_code=500, detail=f"YouTube upload failed for video {i+1}: {e}")

            try:
                os.remove(script_path)
                os.remove(video_path)
                logger.info(f"Cleaned up {script_path}, {video_path}")
            except Exception as e:
                logger.warning(f"Cleanup warning: {e}")

        return {"status": "success", "uploaded_videos": results}

    except Exception as e:
        logger.error(f"Pipeline unexpected error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {e}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    logger.info(f"Starting local server on port {port}...")
    uvicorn.run("app:app", host="0.0.0.0", port=port, log_level="info")
