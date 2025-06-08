import os
import random
import time
from datetime import datetime, timedelta
import logging
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import openai
from googleapiclient.http import MediaFileUpload
from PIL import Image, ImageDraw, ImageFont
import textwrap
import requests
from pexels_api import API
import subprocess
import json
import google.generativeai as genai

# 환경 변수 설정 (10개 키 로테이션)
OPENAI_API_KEYS = os.getenv('OPENAI_API_KEYS', '').split(',')
PEXELS_API_KEY = os.getenv('PEXELS_API_KEY', '')
YOUTUBE_CREDS = {
    'client_id': os.getenv('YOUTUBE_CLIENT_ID', ''),
    'client_secret': os.getenv('YOUTUBE_CLIENT_SECRET', ''),
    'refresh_token': os.getenv('YOUTUBE_REFRESH_TOKEN', '')
}
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY', '')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

# 로깅 설정 (에러 발생 시 알림)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/youtube_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class YouTubeAutomation:
    def __init__(self):
        self.setup_apis()
        self.last_upload_time = None
        
    def setup_apis(self):
        """모든 API 초기화 (에러 발생 시 자동 재시도)"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.current_openai_key = random.choice(OPENAI_API_KEYS)
                openai.api_key = self.current_openai_key
                
                # Gemini 초기화
                genai.configure(api_key=GEMINI_API_KEY)
                self.gemini = genai.GenerativeModel('gemini-pro')
                
                # Pexels API
                self.pexels_api = API(PEXELS_API_KEY)
                
                # YouTube API
                self.youtube = self.setup_youtube_client()
                return
            except Exception as e:
                logger.error(f"API setup attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(5)
    
    def rotate_openai_key(self):
        """OpenAI 키 로테이션 (무료 계정 대비)"""
        available_keys = [k for k in OPENAI_API_KEYS if k != self.current_openai_key]
        if available_keys:
            self.current_openai_key = random.choice(available_keys)
            openai.api_key = self.current_openai_key
            logger.info(f"Rotated to new OpenAI API key (last 4): ...{self.current_openai_key[-4:]}")
    
    def setup_youtube_client(self):
        """YouTube API 클라이언트 설정"""
        creds = Credentials.from_authorized_user_info({
            **YOUTUBE_CREDS,
            'token_uri': 'https://oauth2.googleapis.com/token',
            'scopes': ['https://www.googleapis.com/auth/youtube.upload']
        })
        return build('youtube', 'v3', credentials=creds)
    
    def generate_content(self, topic):
        """AI로 콘텐츠 생성 (GPT-4o와 Gemini 교체 사용)"""
        try:
            # 50% 확률로 GPT-4o 또는 Gemini 사용
            if random.random() < 0.5:
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "Create viral YouTube scripts with emojis. Be engaging!"},
                        {"role": "user", "content": f"Create a 3-minute YouTube script about {topic} with:\n1. Hook intro\n2. 3 main points\n3. Call-to-action\n\nScript:"}
                    ],
                    temperature=0.8
                )
                return response.choices[0].message['content']
            else:
                response = self.gemini.generate_content(
                    f"Create a viral YouTube script about {topic} with:\n1. Hook intro\n2. 3 main points\n3. Call-to-action")
                return response.text
        except Exception as e:
            logger.error(f"AI error: {str(e)}")
            self.rotate_openai_key()
            return self.generate_content(topic)
    
    def generate_thumbnail(self, title):
        """자동 썸네일 생성 (고급 버전)"""
        try:
            # Pexels에서 관련 이미지 검색
            self.pexels_api.search(title, page=1, results_per_page=1)
            photo = self.pexels_api.get_entries()[0]
            img_url = photo.original
            img_data = requests.get(img_url).content
            
            with open("background.jpg", "wb") as f:
                f.write(img_data)
            
            # 이미지에 텍스트 추가
            img = Image.open("background.jpg").resize((1280, 720))
            draw = ImageDraw.Draw(img)
            
            # 폰트 설정 (크기 조정)
            font_size = 60 if len(title) < 30 else 40
            font = ImageFont.truetype("fonts/Catfont.ttf", font_size)
            
            # 텍스트 그림자 효과
            lines = textwrap.wrap(title, width=20)
            y_text = 200
            for line in lines:
                width, height = draw.textsize(line, font=font)
                x = (1280 - width) / 2
                
                # 그림자
                draw.text((x-2, y_text-2), line, font=font, fill=(0,0,0))
                draw.text((x+2, y_text+2), line, font=font, fill=(0,0,0))
                
                # 메인 텍스트
                draw.text((x, y_text), line, font=font, fill=(255, 215, 0))  # 금색
                y_text += height + 10
            
            # 저장
            thumbnail_path = "thumbnail.png"
            img.save(thumbnail_path)
            return thumbnail_path
        except Exception as e:
            logger.error(f"Thumbnail error: {str(e)}")
            return None
    
    def create_video(self, script):
        """FFmpeg로 동영상 생성 (실제 구현 예시)"""
        try:
            # 음성 생성 (간단한 예시)
            with open("script.txt", "w") as f:
                f.write(script)
            
            # FFmpeg 명령어 (실제 구현에서는 더 복잡함)
            cmd = f"ffmpeg -y -f lavfi -i color=c=blue:s=1280x720:d=60 -i thumbnail.png \
                  -filter_complex \"[0:v][1:v]overlay=0:0,drawtext=textfile=script.txt:fontfile=fonts/Catfont.ttf:fontsize=24:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2\" \
                  -c:a aac -strict experimental output.mp4"
            
            subprocess.run(cmd, shell=True, check=True)
            return "output.mp4"
        except Exception as e:
            logger.error(f"Video creation error: {str(e)}")
            return None
    
    def upload_video(self, file_path, title, description, tags):
        """YouTube 업로드 (재시도 로직 추가)"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                request = self.youtube.videos().insert(
                    part="snippet,status",
                    body={
                        "snippet": {
                            "title": title,
                            "description": description[:5000],
                            "tags": tags,
                            "categoryId": "28"  # 과학/기술
                        },
                        "status": {
                            "privacyStatus": "public",
                            "selfDeclaredMadeForKids": False
                        }
                    },
                    media_body=MediaFileUpload(file_path, chunksize=-1, resumable=True)
                )
                
                response = None
                while response is None:
                    status, response = request.next_chunk()
                    if status:
                        logger.info(f"Upload progress: {int(status.progress() * 100)}%")
                
                logger.info(f"Upload complete! Video ID: {response['id']}")
                return response['id']
            except HttpError as e:
                logger.error(f"YouTube upload attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    return None
                time.sleep(10)
    
    def optimize_title(self, title):
        """AI로 제목 최적화 (클릭률 증가)"""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Make YouTube titles more clickable with emojis."},
                    {"role": "user", "content": f"Improve this title for more clicks: {title}"}
                ],
                temperature=0.7
            )
            return response.choices[0].message['content']
        except:
            return title
    
    def daily_upload(self):
        """매일 업로드 메인 로직"""
        if self.last_upload_time and (datetime.now() - self.last_upload_time) < timedelta(hours=20):
            logger.info("Skipping upload (too soon after last upload)")
            return False
            
        try:
            # 트렌딩 주제 선택
            topics = self.get_trending_topics()
            topic = random.choice(topics)
            
            # 콘텐츠 생성
            logger.info(f"Creating content about: {topic}")
            script = self.generate_content(topic)
            
            # 제목 생성 및 최적화
            base_title = f"{topic} - {datetime.now().strftime('%Y.%m.%d')}"
            title = self.optimize_title(base_title)
            
            # 썸네일 생성
            thumbnail = self.generate_thumbnail(title)
            
            # 동영상 생성
            video_path = self.create_video(script)
            
            if video_path and thumbnail:
                # 업로드
                video_id = self.upload_video(
                    video_path,
                    title,
                    script + "\n\n#shorts #viral #trending",
                    [topic.lower(), "ai", "automation"]
                )
                
                if video_id:
                    # 썸네일 설정
                    self.youtube.thumbnails().set(
                        videoId=video_id,
                        media_body=MediaFileUpload(thumbnail)
                    ).execute()
                    
                    # 초기 조회수 증가를 위한 조치
                    self.watch_video(video_id)
                    
                    self.last_upload_time = datetime.now()
                    logger.info(f"Successfully uploaded: {title}")
                    return True
        except Exception as e:
            logger.error(f"Daily upload failed: {str(e)}")
        return False
    
    def get_trending_topics(self):
        """현재 트렌드 주제 가져오기 (실제로는 API 사용)"""
        return [
            "AI News", "Tech Hacks", "Coding Tips",
            "Productivity Tricks", "Science Facts", "Life Improvements"
        ]
    
    def watch_video(self, video_id):
        """초기 조회수 증가를 위해 비디오 시뮬레이션"""
        try:
            requests.get(f"https://www.youtube.com/watch?v={video_id}", timeout=5)
            logger.info(f"Simulated view for video {video_id}")
        except:
            pass

def main():
    automation = YouTubeAutomation()
    automation.daily_upload()

if __name__ == "__main__":
    main()
