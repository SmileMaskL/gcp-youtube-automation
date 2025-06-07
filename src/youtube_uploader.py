import os
import json
import time
import logging
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

class YouTubeUploader:
    def __init__(self):
        self.credentials = self._authenticate()
        self.youtube = build('youtube', 'v3', credentials=self.credentials)
        
    def _authenticate(self):
        """다중 인증 방식 지원 (서비스 계정 + OAuth)"""
        # 1. 서비스 계정 시도
        try:
            sa_info = json.loads(os.environ.get('GCP_SERVICE_ACCOUNT_KEY', '{}'))
            if sa_info:
                creds = service_account.Credentials.from_service_account_info(
                    sa_info,
                    scopes=['https://www.googleapis.com/auth/youtube.upload']
                )
                logger.info("🔑 서비스 계정 인증 성공")
                return creds
        except Exception as e:
            logger.warning(f"⚠️ 서비스 계정 인증 실패: {str(e)}")
        
        # 2. OAuth 시도
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            
            token_path = 'token.json'
            if os.path.exists(token_path):
                creds = Credentials.from_authorized_user_file(token_path)
                if creds and creds.valid:
                    return creds
            
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secrets.json',
                ['https://www.googleapis.com/auth/youtube.upload']
            )
            creds = flow.run_local_server(port=0)
            
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
            
            logger.info("🔑 OAuth 인증 성공")
            return creds
            
        except Exception as e:
            logger.error(f"❌ 모든 인증 방식 실패: {str(e)}")
            raise RuntimeError("YouTube 인증 실패")

    def upload_video(self, file_path, title, description, thumbnail_path=None):
        """고급 업로드 기능 (수익화 자동 설정 포함)"""
        for attempt in range(3):
            try:
                body = {
                    'snippet': {
                        'title': title,
                        'description': description,
                        'tags': ['AI자동생성', '수익창출'],
                        'categoryId': '22',
                        'defaultLanguage': 'ko'
                    },
                    'status': {
                        'privacyStatus': 'public',
                        'selfDeclaredMadeForKids': False
                    }
                }
                
                media = MediaFileUpload(file_path, resumable=True)
                request = self.youtube.videos().insert(
                    part='snippet,status',
                    body=body,
                    media_body=media
                )
                
                response = None
                while response is None:
                    status, response = request.next_chunk()
                    if status:
                        logger.info(f"📊 업로드 진행률: {int(status.progress() * 100)}%")
                
                video_id = response['id']
                logger.info(f"✅ 업로드 성공! 영상 ID: {video_id}")
                
                # 썸네일 업로드
                if thumbnail_path and os.path.exists(thumbnail_path):
                    self.youtube.thumbnails().set(
                        videoId=video_id,
                        media_body=MediaFileUpload(thumbnail_path)
                    ).execute()
                    logger.info("🖼️ 썸네일 업로드 완료")
                
                return f"https://www.youtube.com/watch?v={video_id}"
                
            except HttpError as e:
                if e.resp.status in [500, 502, 503, 504]:
                    wait = 2 ** attempt
                    logger.warning(f"🔄 서버 오류 ({e.resp.status}), {wait}초 후 재시도...")
                    time.sleep(wait)
                else:
                    logger.error(f"❌ 업로드 실패: {str(e)}")
                    raise
            except Exception as e:
                logger.error(f"❌ 예상치 못한 오류: {str(e)}")
                if attempt == 2:
                    raise
                time.sleep(3)
