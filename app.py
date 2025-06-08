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
from typing import List, Dict, Optional

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/youtube_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class YouTubeUploader:
    def __init__(self):
        self.openai_keys = os.getenv('OPENAI_API_KEYS', '').split(',')
        self.current_openai_key = random.choice(self.openai_keys)
        openai.api_key = self.current_openai_key
        
        # Gemini 설정
        genai.configure(api_key=os.getenv('GEMINI_API_KEY', ''))
        self.gemini = genai.GenerativeModel('gemini-pro')
        
        # Pexels 설정
        self.pexels = API(os.getenv('PEXELS_API_KEY', ''))
        
        # YouTube 설정
        self.youtube = self._setup_youtube_client()
        self.last_upload_time = None

    def _setup_youtube_client(self):
        """YouTube 클라이언트 설정"""
        creds = Credentials.from_authorized_user_info({
            'client_id': os.getenv('YOUTUBE_CLIENT_ID', ''),
            'client_secret': os.getenv('YOUTUBE_CLIENT_SECRET', ''),
            'refresh_token': os.getenv('YOUTUBE_REFRESH_TOKEN', ''),
            'token_uri': 'https://oauth2.googleapis.com/token',
            'scopes': ['https://www.googleapis.com/auth/youtube.upload']
        })
        return build('youtube', 'v3', credentials=creds)

    def _rotate_openai_key(self):
        """OpenAI 키 로테이션"""
        available_keys = [k for k in self.openai_keys if k != self.current_openai_key]
        if available_keys:
            self.current_openai_key = random.choice(available_keys)
            openai.api_key = self.current_openai_key
            logger.info(f"Rotated OpenAI key to: ...{self.current_openai_key[-4:]}")

    def _generate_script(self, topic: str) -> str:
        """AI로 스크립트 생성 (GPT-4o와 Gemini 혼용)"""
        try:
            # 50% 확률로 GPT-4o 또는 Gemini 사용
            if random.random() < 0.5:
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a viral YouTube script writer. Create engaging 60-second scripts."},
                        {"role": "user", "content": f"Create a viral YouTube Shorts script about {topic} with:\n1. Hook in first 3 seconds\n2. 3 main points\n3. Call-to-action\n\nScript:"}
                    ],
                    temperature=0.8
                )
                return response.choices[0].message['content']
            else:
                response = self.gemini.generate_content(
                    f"Create a viral 60-second YouTube Shorts script about {topic} with:\n"
                    "1. Hook in first 3 seconds\n2. 3 main points\n3. Call-to-action\n\n"
                    "Include emojis and be very engaging!")
                return response.text
        except Exception as e:
            logger.error(f"Script generation failed: {str(e)}")
            self._rotate_openai_key()
            return self._generate_script(topic)

    def _create_thumbnail(self, title: str) -> Optional[str]:
        """고급 썸네일 생성"""
        try:
            # Pexels에서 배경 이미지 가져오기
            self.pexels.search(title.split()[0], page=1, results_per_page=1)
            photo = self.pexels.get_entries()[0]
            img_response = requests.get(photo.original, timeout=10)
            img_response.raise_for_status()
            
            with open("bg.jpg", "wb") as f:
                f.write(img_response.content)
            
            # 이미지 편집
            img = Image.open("bg.jpg").resize((1280, 720))
            draw = ImageDraw.Draw(img)
            
            # 폰트 크기 자동 조정
            font_size = 60 if len(title) < 25 else 40
            font = ImageFont.truetype("fonts/Catfont.ttf", font_size)
            
            # 텍스트 그림자 효과
            lines = textwrap.wrap(title, width=20)
            y_pos = 180
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                width, height = bbox[2] - bbox[0], bbox[3] - bbox[1]
                x_pos = (1280 - width) / 2
                
                # 그림자
                draw.text((x_pos-2, y_pos-2), line, font=font, fill="black")
                draw.text((x_pos+2, y_pos+2), line, font=font, fill="black")
                
                # 메인 텍스트 (금색)
                draw.text((x_pos, y_pos), line, font=font, fill="#FFD700")
                y_pos += height + 15
            
            # 저장
            thumbnail_path = "thumbnail.png"
            img.save(thumbnail_path)
            return thumbnail_path
        except Exception as e:
            logger.error(f"Thumbnail creation failed: {str(e)}")
            return None

    def _generate_video(self, script: str) -> Optional[str]:
        """FFmpeg로 동영상 생성 (실제 구현 예시)"""
        try:
            # 스크립트 저장
            with open("script.txt", "w") as f:
                f.write(script)
            
            # FFmpeg 명령어 (실제 구현에서는 더 복잡함)
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", "color=c=blue:s=1280x720:d=60",
                "-i", "thumbnail.png",
                "-filter_complex", 
                "[0:v][1:v]overlay=0:0,drawtext=textfile=script.txt:fontfile=fonts/Catfont.ttf:fontsize=24:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
                "-c:a", "aac", "-strict", "experimental",
                "output.mp4"
            ]
            
            subprocess.run(cmd, check=True)
            return "output.mp4"
        except Exception as e:
            logger.error(f"Video generation failed: {str(e)}")
            return None

    def _upload_to_youtube(self, file_path: str, title: str, description: str, tags: List[str]) -> Optional[str]:
        """YouTube에 업로드 (재시도 로직 포함)"""
        for attempt in range(3):
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
                logger.error(f"Upload attempt {attempt + 1} failed: {str(e)}")
                if attempt == 2:
                    return None
                time.sleep(10)

    def _optimize_title(self, title: str) -> str:
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

    def _get_trending_topics(self) -> List[str]:
        """트렌딩 주제 목록 (실제로는 API로 가져옴)"""
        return [
            "AI News Today", "Tech Life Hacks", "Coding Secrets",
            "Productivity Tricks", "Amazing Science Facts", "Life Improvement Tips",
            "Future Technology", "Programming Shortcuts", "Digital Nomad Life"
        ]

    def daily_upload(self) -> bool:
        """매일 업로드 메인 함수"""
        if self.last_upload_time and (datetime.now() - self.last_upload_time) < timedelta(hours=20):
            logger.info("Skipping upload (too soon after last upload)")
            return False
            
        try:
            # 주제 선택
            topic = random.choice(self._get_trending_topics())
            logger.info(f"Selected topic: {topic}")
            
            # 콘텐츠 생성
            script = self._generate_script(topic)
            
            # 제목 최적화
            base_title = f"{topic} - {datetime.now().strftime('%b %d')}"
            title = self._optimize_title(base_title)
            
            # 썸네일 생성
            thumbnail = self._create_thumbnail(title)
            if not thumbnail:
                raise Exception("Failed to create thumbnail")
            
            # 동영상 생성
            video_path = self._generate_video(script)
            if not video_path:
                raise Exception("Failed to create video")
            
            # YouTube 업로드
            video_id = self._upload_to_youtube(
                video_path,
                title,
                f"{script}\n\n#shorts #viral #trending #ai #automation",
                [topic.lower().replace(" ", ""), "ai", "automation", "shorts"]
            )
            
            if video_id:
                # 썸네일 설정
                self.youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(thumbnail)
                ).execute()
                
                # 초기 조회수 부스팅
                self._simulate_view(video_id)
                
                self.last_upload_time = datetime.now()
                logger.info(f"Successfully uploaded: {title}")
                return True
        except Exception as e:
            logger.error(f"Daily upload failed: {str(e)}")
        return False

    def _simulate_view(self, video_id: str):
        """초기 조회수 부스팅 (간단한 버전)"""
        try:
            requests.get(
                f"https://www.youtube.com/watch?v={video_id}",
                timeout=5,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            logger.info(f"Simulated view for video {video_id}")
        except:
            pass

def main():
    uploader = YouTubeUploader()
    uploader.daily_upload()

if __name__ == "__main__":
    main()
