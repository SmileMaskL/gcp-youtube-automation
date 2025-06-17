from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
import os
from pathlib import Path

def upload_to_youtube(video_path, title):
    creds = Credentials.from_authorized_user_info(
        info=json.loads(os.getenv("YOUTUBE_OAUTH_CREDENTIALS")),
        scopes=["https://www.googleapis.com/auth/youtube.upload"]
    )
    
    youtube = build("youtube", "v3", credentials=creds)
    
    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": "자동 생성된 YouTube Shorts",
                "categoryId": "22"
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False
            }
        },
        media_body=MediaFileUpload(str(video_path))
    
    response = request.execute()
    return response
