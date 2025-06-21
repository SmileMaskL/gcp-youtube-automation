# src/youtube_uploader.py
import os
import io
import httplib2
import logging
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

logger = logging.getLogger(__name__)

# YouTube API 스코프
SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube.force-ssl",
          "https://www.googleapis.com/auth/youtube.readonly"]

# 클라이언트 시크릿 JSON 파일 경로를 직접 지정하는 대신, Secret Manager에서 받은 값을 사용
# TOKEN_FILE = "token.json" # 이 파일은 Cloud Functions에서 영구 저장되지 않으므로 사용 불가

class YouTubeUploader:
    def __init__(self, client_id, client_secret, refresh_token):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.youtube = self._get_authenticated_service()

    def _get_authenticated_service(self):
        """YouTube API 서비스에 인증하고 빌드합니다."""
        if not all([self.client_id, self.client_secret, self.refresh_token]):
            logger.error("YouTube API credentials (client_id, client_secret, refresh_token) are missing.")
            raise ValueError("YouTube API credentials are required for authentication.")

        # refresh_token을 사용하여 새 액세스 토큰을 얻습니다.
        # client_secrets_file 없이 직접 credential 객체 생성
        credentials = Credentials(
            token=None,  # 액세스 토큰은 리프레시 토큰으로 갱신될 예정
            refresh_token=self.refresh_token,
            client_id=self.client_id,
            client_secret=self.client_secret,
            token_uri="https://oauth2.googleapis.com/token",
            scopes=SCOPES
        )

        try:
            # 토큰 갱신 시도 (만료되었거나 유효하지 않은 경우)
            credentials.refresh(httplib2.Http())
            logger.info("YouTube API credentials successfully refreshed.")
        except Exception as e:
            logger.error(f"Failed to refresh YouTube access token: {e}")
            raise RuntimeError(f"YouTube authentication failed: {e}")

        return build("youtube", "v3", credentials=credentials)

    def upload_video(self, video_file_path, title, description, tags, privacy_status="private", thumbnail_file_path=None):
        """YouTube에 영상을 업로드합니다."""
        if not os.path.exists(video_file_path):
            logger.error(f"Video file not found: {video_file_path}")
            return None
        
        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": "22" # People & Blogs 카테고리
            },
            "status": {
                "privacyStatus": privacy_status
            }
        }

        # 비디오 파일 업로드
        media_body = MediaFileUpload(video_file_path, mimetype="video/mp4", chunksize=-1, resumable=True)

        try:
            request = self.youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media_body
            )
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    logger.info(f"Uploaded {int(status.resumable_progress * 100)}% of video.")

            video_id = response.get("id")
            logger.info(f"Video '{title}' uploaded. Video Id: {video_id}")

            # 썸네일 업로드
            if thumbnail_file_path and os.path.exists(thumbnail_file_path):
                thumbnail_media = MediaFileUpload(thumbnail_file_path, mimetype="image/jpeg", resumable=True)
                request_thumbnail = self.youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=thumbnail_media
                )
                response_thumbnail = request_thumbnail.execute()
                logger.info(f"Thumbnail uploaded for video Id: {video_id}")
            else:
                logger.warning("Thumbnail file not provided or not found. Skipping thumbnail upload.")

            return video_id

        except HttpError as e:
            logger.error(f"An HTTP error {e.resp.status} occurred: {e.content}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during YouTube upload: {e}", exc_info=True)
            return None

# 로컬에서 리프레시 토큰을 얻는 스크립트 (Cloud Functions 배포 시에는 실행되지 않음)
if __name__ == "__main__":
    # OAuth 클라이언트 ID와 시크릿은 GCP 콘솔에서 데스크톱 앱 유형으로 생성해야 합니다.
    # 이 파일을 실행하기 전에 'client_secrets.json' 파일을 생성해야 합니다.
    # 형식:
    # {
    #   "installed": {
    #     "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
    #     "client_secret": "YOUR_CLIENT_SECRET",
    #     "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
    #     "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    #     "token_uri": "https://oauth2.googleapis.com/token"
    #   }
    # }
    
    # 이 부분은 로컬에서 리프레시 토큰을 한 번 얻기 위해 사용됩니다.
    # 실제 Cloud Function에서는 config에서 이미 로드된 refresh_token을 사용합니다.
    CLIENT_SECRETS_FILE = "youtube_credentials.json" # 이 파일명을 GCP에서 다운로드한 JSON 파일명으로 변경하세요.

    # token.json이 이미 존재하면 로드 (이전 세션에서 인증 정보가 저장된 경우)
    credentials = None
    # if os.path.exists(TOKEN_FILE):
    #     credentials = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(httplib2.Http())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            credentials = flow.run_local_server(port=0) # 포트를 자동으로 할당하여 실행
        
        # 새 또는 갱신된 토큰 저장
        # with open(TOKEN_FILE, 'w') as token:
        #     token.write(credentials.to_json())
        
        print("\n--- Your YouTube Refresh Token ---")
        print("이 토큰을 GitHub Secret Manager (youtube-refresh-token)에 저장하세요.")
        print(credentials.refresh_token)
        print("----------------------------------\n")
    
    # 여기서 업로드 테스트 등도 가능
    # uploader = YouTubeUploader(credentials.client_id, credentials.client_secret, credentials.refresh_token)
    # uploader.upload_video(...)
