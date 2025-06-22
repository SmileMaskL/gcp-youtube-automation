# src/youtube_uploader.py (수정 및 보완된 전체 코드)

import os
import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# YouTube Data API 스코프
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

class YouTubeUploader:
    def __init__(self, client_id, client_secret, refresh_token, project_id, bucket_name):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.project_id = project_id
        self.bucket_name = bucket_name
        self.youtube = self._get_authenticated_service()

    def _get_authenticated_service(self):
        logger.info("YouTube API 인증 시도...")
        try:
            # Refresh Token을 사용하여 자격 증명 생성
            credentials = google.oauth2.credentials.Credentials(
                token=None,  # Access token은 refresh token으로 자동으로 갱신됩니다.
                refresh_token=self.refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=SCOPES
            )
            
            # 자격 증명 갱신 (만료되었을 경우)
            credentials.refresh(google.auth.transport.requests.Request())

            logger.info("YouTube API 자격 증명 갱신 및 빌드 성공.")
            return build(API_SERVICE_NAME, API_VERSION, credentials=credentials)
        except Exception as e:
            logger.error(f"YouTube API 인증 중 오류 발생: {e}", exc_info=True)
            raise

    def upload_video(self, file_path, title, description, tags, privacy_status='private'):
        if not os.path.exists(file_path):
            logger.error(f"영상 파일이 존재하지 않습니다: {file_path}")
            raise FileNotFoundError(f"'{file_path}' 경로에 영상 파일이 없습니다.")

        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags,
                'categoryId': '28' # 카테고리 ID (28은 과학기술, 24는 엔터테인먼트 등)
            },
            'status': {
                'privacyStatus': privacy_status,
                'selfDeclaredMadeForKids': False, # 아동용 콘텐츠 여부
                'for_shorts': True # YouTube Shorts로 지정 (매우 중요!)
            }
        }

        # MediaFileUpload를 사용하여 파일 업로드 준비
        media_body = MediaFileUpload(file_path, chunksize=-1, resumable=True)

        try:
            logger.info(f"YouTube에 영상 업로드 시작: {title}")
            insert_request = self.youtube.videos().insert(
                part='snippet,status',
                body=body,
                media_body=media_body
            )
            response = insert_request.execute()
            logger.info(f"YouTube 영상 업로드 완료. 영상 ID: {response['id']}")
            return response['id']
        except HttpError as e:
            logger.error(f"YouTube API 업로드 오류: {e.resp.status} - {e.content}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"예상치 못한 업로드 오류: {e}", exc_info=True)
            raise
