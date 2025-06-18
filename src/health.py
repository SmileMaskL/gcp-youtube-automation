from fastapi import FastAPI
import os
import logging

app = FastAPI()
PORT = int(os.getenv("PORT", "8080"))

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.get("/health")
def health_check():
    logger.info(f"Health check on port {PORT}")
    return {"status": "ok", "port": PORT}

@app.get("/")
def home():
    return {"message": "YouTube Automation Service"}
