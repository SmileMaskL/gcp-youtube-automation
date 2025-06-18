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
        # 1. 인증 정보 로드
        creds_json = Config.get_api_key("YOUTUBE_OAUTH_CREDENTIALS")
        if not creds_json:
            raise ValueError("YouTube 인증 정보 없음")
            
        creds = Credentials.from_authorized_user_info(
            json.loads(creds_json),
            scopes=["https://www.googleapis.com/auth/youtube.upload"]
        )
        
        # 2. YouTube API 클라이언트 생성
        youtube = build("youtube", "v3", credentials=creds)
        
        # 3. 자동 생성된 해시태그 추가
        hashtags = [
            "#Shorts", "#유튜브자동화", "#트렌드",
            "#" + title.replace(" ", ""), "#자동생성영상"
        ]
        
    """60초 Shorts 전용 업로드"""
    request_body = {
        "snippet": {
            "title": f"{content['title']} #shorts",
            "description": f"오늘의 핫이슈! {content['title']}\n\n{' '.join(content['hashtags'])}",
            "categoryId": "24"  # 엔터테인먼트
        },
        "status": {
            "privacyStatus": "public",
            "madeForKids": False
        },
        "contentDetails": {
            "duration": "PT60S",  # 60초 고정
            "dimension": "portrait",  # 세로 영상
            "definition": "hd"  # 720p 이상
        }
    }
    
    # 업로드 실행
    youtube = build("youtube", "v3", credentials=get_credentials())
    request = youtube.videos().insert(
        part="snippet,status,contentDetails",
        body=request_body,
        media_body=MediaFileUpload(video_path)
    )
        
        response = request.execute()
        logger.info(f"업로드 성공! 영상 ID: {response['id']}")
        return True
        
    except Exception as e:
        logger.error(f"업로드 실패: {e}")
        return False
