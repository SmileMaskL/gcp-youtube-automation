# src/youtube_uploader.py
import os
import logging
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

class YouTubeUploader:
    def __init__(self, client_id: str, client_secret: str, refresh_token: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.youtube = self._get_authenticated_service()

    def _get_authenticated_service(self):
        """
        YouTube API에 인증하고 서비스 객체를 반환합니다.
        제공된 refresh_token을 사용하여 Access Token을 갱신합니다.
        """
        creds = None
        # GitHub Actions에서 환경 변수를 통해 refresh_token을 받으므로, 별도의 credentials.json 파일은 필요 없습니다.
        # 기존 refresh token으로 Credentials 객체를 직접 생성합니다.
        try:
            creds = Credentials(
                token=None,  # Access token은 refresh_token으로 갱신될 것이므로 None으로 설정
                refresh_token=self.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=SCOPES
            )
            
            # Access Token이 만료되었거나 없는 경우 refresh_token을 사용하여 갱신합니다.
            if not creds.valid:
                logging.info("Refreshing YouTube access token...")
                creds.refresh(Request())
                logging.info("YouTube access token refreshed successfully.")

            return build('youtube', 'v3', credentials=creds)

        except Exception as e:
            logging.error(f"Error authenticating to YouTube API: {e}", exc_info=True)
            return None

    def upload_video(self, file_path: str, title: str, description: str, tags: list, privacy_status: str = 'private'):
        """
        지정된 비디오 파일을 YouTube에 업로드합니다.
        """
        if not self.youtube:
            logging.error("YouTube service not authenticated. Cannot upload video.")
            return None
        
        if not os.path.exists(file_path):
            logging.error(f"Video file not found at: {file_path}")
            return None

        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags,
                'categoryId': '28',  # Technology category ID, YouTube Shorts는 보통 Category ID 28 또는 22 (People & Blogs)
                'defaultLanguage': 'en'
            },
            'status': {
                'privacyStatus': privacy_status, # 'public', 'private', 'unlisted'
                'madeForKids': False # Kids content 여부 (필수)
            },
            'recordingDetails': {
                'recordingDate': '2024-01-01T00:00:00Z' # 샘플 날짜, 필요시 동적 생성
            }
        }

        # MediaFileUpload를 사용하여 비디오 파일을 업로드 준비
        media_body = MediaFileUpload(file_path, chunksize=-1, resumable=True)

        try:
            insert_request = self.youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media_body
            )
            response = None
            while response is None:
                status, response = insert_request.next_chunk()
                if status:
                    logging.info(f"Uploaded {int(status.progress() * 100)}%")

            logging.info(f"Video upload successful! Video ID: {response['id']}")
            return response['id']
        except HttpError as e:
            logging.error(f"An HTTP error occurred: {e.resp.status} - {e.content}", exc_info=True)
            return None
        except Exception as e:
            logging.error(f"An unexpected error occurred during video upload: {e}", exc_info=True)
            return None

# OAuth 인증 플로우를 로컬에서 실행하여 refresh_token을 얻는 스크립트
# 이 스크립트는 한 번만 실행하여 YOUTUBE_REFRESH_TOKEN을 얻은 후 GitHub Secret에 저장해야 합니다.
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # 환경 변수에서 CLIENT_ID와 CLIENT_SECRET 로드
    client_id = os.environ.get('YOUTUBE_CLIENT_ID')
    client_secret = os.environ.get('YOUTUBE_CLIENT_SECRET')

    if not client_id or not client_secret:
        logging.error("YOUTUBE_CLIENT_ID or YOUTUBE_CLIENT_SECRET environment variables are not set.")
        logging.info("Please set these variables to run the OAuth flow.")
        exit(1)

    flow = InstalledAppFlow.from_client_secrets_file(
        # client_secrets.json 파일은 Google Cloud Console에서 다운로드한 OAuth 2.0 클라이언트 ID JSON 파일입니다.
        # 이 파일은 로컬 실행 시에만 필요하며, 실제 워크플로우에서는 환경 변수로 직접 refresh_token을 사용합니다.
        # client_secrets.json 파일이 없으면 이 스크립트는 실행될 수 없습니다.
        # 실제 파일 경로에 맞게 수정해주세요.
        # 예: 'client_secrets.json'
        # 주의: 이 파일은 GitHub에 올리면 안 됩니다!
        'path/to/your/client_secrets.json', # <--- 여기에 실제 client_secrets.json 파일 경로를 넣어주세요!
        SCOPES
    )
    # 로컬 서버를 통해 인증을 진행합니다.
    credentials = flow.run_local_server(port=0)

    print(f"Credentials generated successfully. Save the following refresh token to your GitHub Secrets (YOUTUBE_REFRESH_TOKEN):\n")
    print(credentials.refresh_token)

    # 이 refresh_token을 GitHub Secrets에 YOUTUBE_REFRESH_TOKEN으로 저장합니다.
    # 이후에는 이 스크립트를 다시 실행할 필요가 없습니다.
