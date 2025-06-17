from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
import os
import json
from pathlib import Path
import logging

# 로거 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_quota(youtube):
    quota = youtube.quota().get().execute()
    logger.info(f"현재 API 쿼터: {quota}")

def upload_to_youtube(video_path, title):
    """YouTube에 동영상 업로드"""
    try:
        # 환경 변수에서 인증 정보 로드
        creds_json = os.getenv("YOUTUBE_OAUTH_CREDENTIALS")
        if not creds_json:
            raise ValueError("YouTube OAuth credentials not found in environment variables")
        
        # Credentials 객체 생성
        creds = Credentials.from_authorized_user_info(
            info=json.loads(creds_json),
            scopes=["https://www.googleapis.com/auth/youtube.upload"]
        )
        
        # YouTube API 서비스 빌드
        youtube = build("youtube", "v3", credentials=creds)
        
        # 업로드 요청 본문
        request_body = {
            "snippet": {
                "title": title,
                "description": "자동 생성된 YouTube Shorts 영상",
                "categoryId": "22"  # 엔터테인먼트 카테고리
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False
            }
        }
        
        # 미디어 파일 업로드 객체 생성
        media = MediaFileUpload(
            str(video_path),
            mimetype="video/mp4",
            resumable=True
        )
        
        # API 요청 실행
        request = youtube.videos().insert(
            part="snippet,status",
            body=request_body,
            media_body=media
        )
        
        response = request.execute()
        logger.info(f"영상 업로드 성공: {response['id']}")
        return True
        
    except Exception as e:
        logger.error(f"영상 업로드 실패: {str(e)}")
        return False
