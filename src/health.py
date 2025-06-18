from fastapi import FastAPI
import os
import logging

app = FastAPI()
PORT = int(os.getenv("PORT", "8080"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.get("/health")
def health_check():
    logger.info(f"✅ Health check passed on port {PORT}")
    return {
        "status": "healthy",
        "service": "youtube-automation",
        "port": PORT
    }

@app.get("/")
def home():
    return {"status": "running", "docs": "/docs"}
