import os
import uuid
import random
import requests
import logging
from pathlib import Path
from dotenv import load_dotenv
import subprocess
import shutil
from datetime import datetime
import time
import json

# 로거 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('youtube_shorts.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

class Config:
    TEMP_DIR = Path("temp")  # 수정: /tmp 대신 상대경로
    OUTPUT_DIR = Path("output")
    SHORTS_WIDTH = 1080
    SHORTS_HEIGHT = 1920
    FONT_PATH = "fonts/Catfont.ttf"  # 수정: 상대경로 사용
    VIDEO_DURATION = 60
    
    @staticmethod
    def get_api_key(key_name):
        return os.environ[key_name]  # 수정: dotenv 대신 직접 접근

    @classmethod
    def initialize(cls):
        cls.TEMP_DIR.mkdir(parents=True, exist_ok=True)
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 수정: 간소화된 트렌딩 주제 생성
def get_trending_topics():
    return [
        {
            "title": "인공지능의 미래",
            "script": "AI는 2025년 현재 모든 산업을 혁신 중입니다. 특히 의료 분야에서 큰 진전을 보이고 있어요!",
            "pexel_query": "technology future"
        },
        {
            "title": "지속 가능한 에너지",
            "script": "태양광과 풍력 에너지가 전 세계 전력의 30%를 공급하고 있습니다. 청정 에너지로 가는 길!",
            "pexel_query": "sustainable energy"
        }
    ]

# 수정: ElevenLabs 음성 생성
def generate_tts(script):
    audio_path = Config.TEMP_DIR / f"audio_{uuid.uuid4()}.mp3"
    headers = {"xi-api-key": Config.get_api_key("ELEVENLABS_API_KEY")}
    response = requests.post(
        "https://api.elevenlabs.io/v1/text-to-speech/uyVNoMrnUku1dZyVEXwD",
        headers=headers,
        json={"text": script, "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}},
        timeout=30
    )
    response.raise_for_status()
    with open(audio_path, "wb") as f:
        f.write(response.content)
    return audio_path

# 수정: Pexels 배경 영상 다운로드
def get_background_video(query):
    video_path = Config.TEMP_DIR / f"bg_{uuid.uuid4()}.mp4"
    response = requests.get(
        f"https://api.pexels.com/videos/search?query={query}&per_page=10",
        headers={"Authorization": Config.get_api_key("PEXELS_API_KEY")}
    )
    video = random.choice(response.json()["videos"])
    video_url = next((f["link"] for f in video["video_files"] if f["width"] == Config.SHORTS_WIDTH), None)
    
    with requests.get(video_url, stream=True, timeout=30) as r:
        with open(video_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return video_path

# 수정: Pillow를 이용한 텍스트 렌더링
def render_text_image(title, script, output_path):
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGB", (Config.SHORTS_WIDTH, Config.SHORTS_HEIGHT), "black")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(str(Config.FONT_PATH), 60)
    
    # 제목 렌더링
    draw.text((50, 200), title, font=font, fill="white")
    
    # 대본 렌더링 (줄바꿈 처리)
    y_offset = 400
    for line in textwrap.wrap(script, width=40):
        draw.text((50, y_offset), line, font=font, fill="white")
        y_offset += 70
    
    img.save(output_path)

# 수정: FFmpeg 오버레이 방식 변경
def create_video(content, audio_path, bg_path):
    output_path = Config.OUTPUT_DIR / f"shorts_{uuid.uuid4()}.mp4"
    text_image = Config.TEMP_DIR / f"text_{uuid.uuid4()}.png"
    
    # 텍스트 이미지 생성
    render_text_image(content["title"], content["script"], text_image)
    
    # FFmpeg 명령어 실행
    subprocess.run([
        "ffmpeg",
        "-i", str(bg_path),
        "-i", str(text_image),
        "-i", str(audio_path),
        "-filter_complex",
        "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[bg];"
        "[bg][1:v]overlay=0:0[vid]",
        "-map", "[vid]",
        "-map", "2:a",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest",
        "-y", str(output_path)
    ], check=True)
    
    return output_path

# 수정: YouTube 업로드 (실제 구현)
def upload_to_youtube(video_path, title):
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    
    creds = None  # 여기에 GCP 인증 정보 추가
    youtube = build("youtube", "v3", credentials=creds)
    
    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": "자동 생성된 YouTube Shorts",
            },
            "status": {"privacyStatus": "public"}
        },
        media_body=MediaFileUpload(str(video_path))
    )
    request.execute()
    return True

def main():
    Config.initialize()
    topics = get_trending_topics()
    
    for topic in topics:
        audio_path = generate_tts(topic["script"])
        bg_path = get_background_video(topic["pexel_query"])
        video_path = create_video(topic, audio_path, bg_path)
        upload_to_youtube(video_path, topic["title"])
        time.sleep(30)

if __name__ == "__main__":
    main()
