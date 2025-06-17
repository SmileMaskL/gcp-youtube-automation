from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
import os
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def upload_to_youtube(video_path, title):
    """YouTube에 영상 업로드"""
    try:
        # 1. 인증 정보 로드
        creds_json = os.getenv("YOUTUBE_OAUTH_CREDENTIALS")
        if not creds_json:
            raise ValueError("YouTube 인증 정보 없음")
            
        creds = Credentials.from_authorized_user_info(
            json.loads(creds_json),
            scopes=["https://www.googleapis.com/auth/youtube.upload"]
        )
        
        # 2. YouTube API 클라이언트 생성
        youtube = build("youtube", "v3", credentials=creds)
        
        # 3. 업로드 요청 본문
        request_body = {
            "snippet": {
                "title": title,
                "description": "자동 생성된 YouTube Shorts 영상",
                "categoryId": "22"  # 엔터테인먼트
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False
            }
        }
        
        # 4. 미디어 파일 업로드 설정
        media = MediaFileUpload(
            str(video_path),
            mimetype="video/mp4",
            resumable=True
        )
        
        # 5. API 요청 실행
        request = youtube.videos().insert(
            part="snippet,status",
            body=request_body,
            media_body=media
        )
        
        response = request.execute()
        logger.info(f"업로드 성공! 영상 ID: {response['id']}")
        return True
        
    except Exception as e:
        logger.error(f"업로드 실패: {e}")
        return False
