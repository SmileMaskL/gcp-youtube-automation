# src/app.py

import os
import logging
import uuid
from datetime import datetime
from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor
import google.generativeai as genai
from googleapiclient.discovery import build
import ffmpeg

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
executor = ThreadPoolExecutor(max_workers=4)
job_status = {}

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
youtube = build("youtube", "v3", developerKey=os.environ.get("YOUTUBE_API_KEY"))

@app.route('/healthz')
def health():
    return jsonify({"status": "ok"})

@app.route("/", methods=["POST"])
def main():
    data = request.get_json()
    action = data.get('action')
    job_id = str(uuid.uuid4())
    job_status[job_id] = {"status": "queued", "start_time": datetime.utcnow().isoformat()}

    if action == "create_and_upload_shorts":
        executor.submit(process_job, job_id)
        return jsonify({"status": "processing", "job_id": job_id}), 202

    return jsonify({"status": "error", "message": "Invalid action"}), 400

def process_job(job_id):
    try:
        script = genai.GenerativeModel("gemini-pro").generate_content("오늘의 명언").text
        video_path = f"output/{job_id}.mp4"
        ffmpeg.input('color=c=black:s=1080x1920', f='lavfi', t=15).output(video_path).run(overwrite_output=True)
        youtube.videos().insert(part="snippet,status", body={"snippet": {"title": script}}, media_body={'body': open(video_path, 'rb')}).execute()
        job_status[job_id]["status"] = "completed"
    except Exception as e:
        job_status[job_id]["status"] = "failed"
        job_status[job_id]["error"] = str(e)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
