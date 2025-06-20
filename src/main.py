# main.py (기존 batch_runner 역할을 대체)
from fastapi import FastAPI, BackgroundTasks
from src.batch_processor import BatchProcessor

app = FastAPI()

@app.get("/run")
def trigger_run(background_tasks: BackgroundTasks):
    background_tasks.add_task(BatchProcessor().process)
    return {"status": "배치 작업이 백그라운드로 시작되었습니다."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
