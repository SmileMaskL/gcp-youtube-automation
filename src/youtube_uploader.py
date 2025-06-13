from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import json
import os

def upload_to_youtube(video_path: str, thumbnail_path: str, title: str):
    """유튜브에 영상 업로드"""
    try:
        # 1. 인증 정보 로드
        creds = Credentials.from_authorized_user_info(
            json.loads(os.getenv("YOUTUBE_OAUTH_CREDENTIALS")),
            ['https://www.googleapis.com/auth/youtube.upload']
        )
        
        # 2. YouTube API 연결
        youtube = build('youtube', 'v3', credentials=creds)
        
        # 3. 영상 업로드
        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                    "description": "AI로 자동 생성된 영상입니다.\n#AI #자동화 #유튜브",
                    "tags": ["AI", "자동화", "유튜브"]
                },
                "status": {
                    "privacyStatus": "public"  # 테스트 시에는 "unlisted"로 변경
                }
            },
            media_body=MediaFileUpload(video_path)
        )
        response = request.execute()
        
        # 4. 썸네일 업로드
        youtube.thumbnails().set(
            videoId=response['id'],
            media_body=MediaFileUpload(thumbnail_path)
        ).execute()
        
        print(f"🎉 업로드 완료! 영상 ID: {response['id']}")
        return response['id']
    except Exception as e:
        print(f"❌ 유튜브 업로드 오류: {e}")
        raise
