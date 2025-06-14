"""
유튜브 자동화 봇 메인 컨트롤러 (2025년 최적화 버전)
"""
import os
from googleapiclient.discovery import build 
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow 
import logging
import time
import json
from pathlib import Path
from datetime import datetime
import random
from dotenv import load_dotenv
import sys
sys.path.append('./src')
from utils import generate_viral_content
from thumbnail_generator import generate_thumbnail
from video_creator import create_final_video
from youtube_uploader import upload_video
from content_generator import get_hot_topics

# 환경변수 로드
load_dotenv()

# 로깅 설정
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/youtube_automation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class YouTubeAutomation:
    def __init__(self):
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.used_topics = set()
        self.load_used_topics()

    def load_used_topics(self):
        if Path("used_topics.json").exists():
            with open("used_topics.json", "r") as f:
                self.used_topics = set(json.load(f))

    def save_used_topics(self):
        with open("used_topics.json", "w") as f:
            json.dump(list(self.used_topics), f)

    def get_fresh_topic(self):
        """중복되지 않은 새로운 주제 가져오기"""
        max_retries = 5
        for _ in range(max_retries):
            topics = get_hot_topics()
            for topic in topics:
                if topic not in self.used_topics:
                    self.used_topics.add(topic)
                    self.save_used_topics()
                    return topic
            time.sleep(2)
        return random.choice(["부자가 되는 습관", "AI로 돈 버는 법", "성공 비결", "재테크 팁"])

    def run(self):
        logger.info("="*50)
        logger.info("💰 유튜브 수익형 자동화 시스템 시작 💰")
        logger.info("="*50)

        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        if not GEMINI_API_KEY:
            logger.error("❌ 오류: GEMINI_API_KEY가 설정되지 않았습니다. .env 파일에 키를 추가하세요.")
            return

        try:
            # 1. 주제 선정
            topic = self.get_fresh_topic()
            logger.info(f"🔥 오늘의 주제: {topic}")

            # 2. 콘텐츠 생성
            content = None
            try:
                content = generate_viral_content(topic)
            except Exception as e:
                logger.error(f"❌ 콘텐츠 생성 실패: {e}")
                return

            script = content.get("script") if content else None
            if not script or len(script) < 50:
                logger.error("❌ 오류: 생성된 스크립트가 없습니다 또는 너무 짧습니다.")
                return
            logger.info(f"📜 생성된 대본 길이: {len(script)}자")

            title = f"{topic}의 비밀"
            hashtags = [f"#{topic.replace(' ', '')}", "#꿀팁", "#자기계발"]
            logger.info(f"📝 생성된 제목: {title}")

            # 3. 썸네일 생성
            thumbnail_path = generate_thumbnail(topic)
            logger.info(f"🖼️ 썸네일 생성 완료: {thumbnail_path}")

            # 4. 영상 생성
            final_video_path = create_final_video(topic, title, script)
            if not final_video_path:
                logger.error("❌ 영상 생성 실패")
                return
            logger.info(f"🎥 영상 생성 완료: {final_video_path}")

            # 5. 유튜브 업로드
            result = upload_video(
                video_path=final_video_path,
                title=f"{title} #shorts",
                description=f"{script}\n\n{' '.join(hashtags)}",
                tags=hashtags,
                privacy_status="public",
                thumbnail_path=thumbnail_path
            )
            if result:
                logger.info("✅ 업로드 성공!")
                Path(final_video_path).unlink(missing_ok=True)
                Path(thumbnail_path).unlink(missing_ok=True)
            else:
                logger.error("❌ 업로드 실패")

        except Exception as e:
            logger.error(f"❌ 전체 시스템 오류: {e}", exc_info=True)

def main():
    automation = YouTubeAutomation()
    automation.run()

if __name__ == "__main__":
    main()

def upload_to_youtube(video_path: str, title: str, description: str):
    try:
        # 환경변수에서 인증 정보 가져오기
        client_secrets = {
            "web": {
                "client_id": os.getenv("YT_CLIENT_ID"),
                "client_secret": os.getenv("YT_CLIENT_SECRET"),
                "redirect_uris": [os.getenv("YT_REDIRECT_URI")],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://accounts.google.com/o/oauth2/token"
            }
        }
        
        # YouTube API 인증
        flow = InstalledAppFlow.from_client_config(
            client_secrets,
            scopes=["https://www.googleapis.com/auth/youtube.upload"]
        )
        
        credentials = flow.run_local_server(port=8080)
        youtube = build('youtube', 'v3', credentials=credentials)
        
        # 영상 업로드
        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": ["shorts", "자동생성"],
                    "categoryId": "22"  # Entertainment
                },
                "status": {
                    "privacyStatus": "public",
                    "selfDeclaredMadeForKids": False
                }
            },
            media_body=MediaFileUpload(video_path)
        )
        
        response = request.execute()
        logger.info(f"✅ 업로드 성공: https://youtu.be/{response['id']}")
        return response
        
    except Exception as e:
        logger.error(f"❌ 업로드 실패: {str(e)}")
        raise
