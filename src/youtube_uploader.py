import os
import google.auth
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from src.config import Config

class YouTubeUploader:
    def __init__(self, credentials: dict):
        self.credentials = credentials
        self.service = self._get_authenticated_service()

    def _get_authenticated_service(self):
        from google.oauth2.credentials import Credentials
        
        creds = Credentials(
            token=self.credentials.get('access_token'),
            refresh_token=self.credentials.get('refresh_token'),
            token_uri=self.credentials.get('token_uri'),
            client_id=self.credentials.get('client_id'),
            client_secret=self.credentials.get('client_secret')
        )
        
        return build('youtube', 'v3', credentials=creds)

    def upload_video(self, file_path: str, title: str, description: str):
        request_body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': ['shorts', '자동생성'],
                'categoryId': '22'
            },
            'status': {
                'privacyStatus': 'public',
                'selfDeclaredMadeForKids': False
            }
        }
        
        media = MediaFileUpload(
            file_path,
            mimetype='video/mp4',
            resumable=True
        )
        
        response = self.service.videos().insert(
            part='snippet,status',
            body=request_body,
            media_body=media
        ).execute()
        
        return response
