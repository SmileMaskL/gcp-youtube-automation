import os
from dotenv import load_dotenv
from pathlib import Path

class Config:
    TEMP_DIR = Path("./temp")
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    SHORTS_WIDTH = 1080
    SHORTS_HEIGHT = 1920

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
GCP_BUCKET_NAME = os.getenv("GCP_BUCKET_NAME")

MAX_DAILY_UPLOADS = 5
