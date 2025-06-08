import os
import random
import time
from datetime import datetime
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

# 환경 변수 설정
OPENAI_API_KEYS = os.getenv('OPENAI_API_KEYS').split(',')
PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')
YOUTUBE_CLIENT_ID = os.getenv('YOUTUBE_CLIENT_ID')
YOUTUBE_CLIENT_SECRET = os.getenv('YOUTUBE_CLIENT_SECRET')
YOUTUBE_REFRESH_TOKEN = os.getenv('YOUTUBE_REFRESH_TOKEN')
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/youtube_automation.log'
)
logger = logging.getLogger(__name__)

class YouTubeAutomation:
    def __init__(self):
        self.current_openai_key = random.choice(OPENAI_API_KEYS)
        openai.api_key = self.current_openai_key
        self.pexels_api = API(PEXELS_API_KEY)
        self.youtube = self.setup_youtube_client()
        
    def rotate_openai_key(self):
        """OpenAI 키 로테이션"""
        available_keys = [k for k in OPENAI_API_KEYS if k != self.current_openai_key]
        if available_keys:
            self.current_openai_key = random.choice(available_keys)
            openai.api_key = self.current_openai_key
            logger.info(f"Rotated to new OpenAI API key (last 4): ...{self.current_openai_key[-4:]}")
    
    def setup_youtube_client(self):
        """YouTube API 클라이언트 설정"""
        creds = Credentials.from_authorized_user_info({
            'client_id': YOUTUBE_CLIENT_ID,
            'client_secret': YOUTUBE_CLIENT_SECRET,
            'refresh_token': YOUTUBE_REFRESH_TOKEN,
            'token_uri': 'https://oauth2.googleapis.com/token',
            'scopes': ['https://www.googleapis.com/auth/youtube.upload']
        })
        return build('youtube', 'v3', credentials=creds)
    
    def generate_content(self, topic):
        """AI로 콘텐츠 생성"""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates engaging YouTube video scripts."},
                    {"role": "user", "content": f"Create a detailed YouTube script about {topic}. Include an attention-grabbing intro, main content with 3-5 key points, and a conclusion with a call to action."}
                ],
                temperature=0.7
            )
            return response.choices[0].message['content']
        except Exception as e:
            logger.error(f"OpenAI error: {str(e)}")
            self.rotate_openai_key()
            return self.generate_content(topic)
    
    def generate_thumbnail(self, title):
        """썸네일 생성"""
        try:
            # 간단한 썸네일 생성 로직 (실제로는 더 복잡하게 구현)
            img = Image.new('RGB', (1280, 720), color=(73, 109, 137))
            d = ImageDraw.Draw(img)
            font = ImageFont.truetype("fonts/Catfont.ttf", 60)
            
            # 제목을 여러 줄로 나누기
            lines = textwrap.wrap(title, width=20)
            y_text = 200
            for line in lines:
                width, height = d.textsize(line, font=font)
                d.text(((1280 - width) / 2, y_text), line, font=font, fill=(255, 255, 0))
                y_text += height + 10
            
            # 저장
            thumbnail_path = "thumbnail.png"
            img.save(thumbnail_path)
            return thumbnail_path
        except Exception as e:
            logger.error(f"Thumbnail generation error: {str(e)}")
            return None
    
    def upload_video(self, file_path, title, description, tags, category_id="22"):
        """YouTube에 동영상 업로드"""
        try:
            request = self.youtube.videos().insert(
                part="snippet,status",
                body={
                    "snippet": {
                        "title": title,
                        "description": description,
                        "tags": tags,
                        "categoryId": category_id
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
                    logger.info(f"Uploaded {int(status.progress() * 100)}%")
            
            logger.info(f"Upload complete! Video ID: {response['id']}")
            return response['id']
        except HttpError as e:
            logger.error(f"YouTube API error: {str(e)}")
            return None
    
    def post_comment(self, video_id, comment_text):
        """동영상에 댓글 달기"""
        try:
            self.youtube.commentThreads().insert(
                part="snippet",
                body={
                    "snippet": {
                        "videoId": video_id,
                        "topLevelComment": {
                            "snippet": {
                                "textOriginal": comment_text
                            }
                        }
                    }
                }
            ).execute()
            logger.info(f"Posted comment on video {video_id}")
        except HttpError as e:
            logger.error(f"Failed to post comment: {str(e)}")
    
    def create_short_video(self, content):
        """쇼츠 형식 동영상 생성"""
        # 실제 구현에서는 FFmpeg 등을 사용해 동영상 생성
        pass
    
    def daily_upload_process(self):
        """일일 업로드 프로세스"""
        try:
            # 인기 주제 선택 (실제로는 트렌드 분석 추가)
            topics = [
                "Tech News", "AI Developments", "Programming Tips", 
                "Life Hacks", "Productivity Tips", "Science Facts"
            ]
            selected_topic = random.choice(topics)
            
            # 콘텐츠 생성
            logger.info(f"Generating content about: {selected_topic}")
            content = self.generate_content(selected_topic)
            
            # 동영상 제목 생성
            title = f"{selected_topic} - {datetime.now().strftime('%Y.%m.%d')}"
            
            # 썸네일 생성
            thumbnail_path = self.generate_thumbnail(title)
            
            # 동영상 생성 (실제로는 FFmpeg 등을 사용해 동영상 생성)
            video_path = "output.mp4"  # 실제로는 생성된 동영상 경로
            
            # YouTube 업로드
            video_id = self.upload_video(
                video_path,
                title,
                content[:5000],  # 설명은 5000자 제한
                selected_topic.lower().split(),
                "28"  # Science & Technology 카테고리
            )
            
            if video_id:
                # 썸네일 설정
                self.youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(thumbnail_path)
                ).execute()
                
                # 댓글 달기
                self.post_comment(video_id, "Thanks for watching! Don't forget to like and subscribe!")
                
                logger.info(f"Successfully uploaded video: {title}")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Daily upload process failed: {str(e)}")
            return False

def main():
    automation = YouTubeAutomation()
    automation.daily_upload_process()

if __name__ == "__main__":
    main()
