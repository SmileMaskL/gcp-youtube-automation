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
        
        # 4. 업로드 요청 본문
        request_body = {
            "snippet": {
                "title": f"{title} | 오늘의 핫이슈",
                "description": f"""이 영상은 자동 생성되었습니다. 오늘의 핫한 주제를 알려드립니다!\n\n{" ".join(hashtags)}\n\n#YouTubeAutomation""",
                "categoryId": "22",  # 엔터테인먼트
                "tags": ["Shorts", "자동생성", "트렌드"]
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False,
                "publishAt": (datetime.now() + timedelta(hours=1)).isoformat() + "Z"  # 1시간 후 공개
            }
        }
        
        # 5. 미디어 파일 업로드
        media = MediaFileUpload(
            str(video_path),
            mimetype="video/mp4",
            resumable=True,
            chunksize=1024*1024
        )
        
        # 6. API 요청 실행
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
