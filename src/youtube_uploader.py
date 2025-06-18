import os
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from pathlib import Path
from .config import Config
import logging

logger = logging.getLogger(__name__)

def upload_to_youtube(video_path, title):
    """YouTube에 영상 업로드"""
    try:
        # 1. 인증 정보 로드 (GitHub Secrets 연동)
        creds = Credentials.from_authorized_user_info(
            json.loads(Config.get_api_key("YOUTUBE_OAUTH_CREDENTIALS")),
            scopes=["https://www.googleapis.com/auth/youtube.upload"]
        )
        
        # 2. Shorts 최적화 메타데이터
        request_body = {
            "snippet": {
                "title": f"{content['title']} #shorts",
                "description": f"🔥 {content['title']} 🔥\n\n{' '.join(content['hashtags'])}\n\n#유튜브자동화",
                "categoryId": "24",  # 엔터테인먼트
                "tags": content["hashtags"] + ["Shorts", "자동생성"]
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False
            },
            "contentDetails": {
                "duration": "PT60S",  # 60초 명시
                "dimension": "portrait",  # 세로 모드
                "definition": "hd"  # 720p 이상
            }
        }
        
        # 3. 업로드 실행
        youtube = build("youtube", "v3", credentials=creds)
        media = MediaFileUpload(video_path, mimetype="video/mp4")
        request = youtube.videos().insert(
            part="snippet,status,contentDetails",
            body=request_body,
            media_body=media
        )
        response = request.execute()
        logger.info(f"업로드 성공! 영상 ID: {response['id']}")
        return True
        
    except Exception as e:
        logger.error(f"업로드 실패: {e}")
        return False
