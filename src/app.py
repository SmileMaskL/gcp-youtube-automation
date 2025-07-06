# src/app.py

from fastapi import FastAPI, Request
import uvicorn

app = FastAPI()

@app.post("/")
async def root(request: Request):
    data = await request.json()
    return {"message": "Received root", "data": data}

@app.post("/generate")
async def generate_content(request: Request):
    data = await request.json()
    # 여기에 AI 콘텐츠 생성 로직 삽입
    return {"message": "Content generated", "data": data}

@app.post("/upload")
async def upload_video(request: Request):
    data = await request.json()
    # 여기에 유튜브 업로드 로직 삽입
    return {"message": "Video uploaded", "data": data}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8080)
