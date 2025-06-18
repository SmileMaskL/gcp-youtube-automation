from fastapi import FastAPI
import os
import logging

app = FastAPI()
PORT = 8080  # 명시적 포트 설정 (Cloud Run 표준)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.get("/health")
def health_check():
    return {"status": "ok", "port": PORT}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
