# src/youtube_uploader.py
import os
import io
import logging
import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

logger = logging.getLogger(__name__)

# 승인된 범위 정의
SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.force-ssl"]

class YouTubeUploader:
    def __init__(self, client_id: str, client_secret: str, refresh_token: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.credentials = self._authenticate_youtube()

    def _authenticate_youtube(self):
        """
        YouTube API 인증을 처리합니다.
        Refresh Token을 사용하여 새 Access Token을 얻습니다.
        """
        creds = None
        # 자격 증명 파일 경로 (Cloud Functions에서는 /tmp에 저장)
        # credentials.json 파일은 초기 인증 시에만 필요하며, refresh_token이 있으면 직접 credential 객체를 생성합니다.
        
        # refresh_token을 사용하여 Credentials 객체 생성
        if self.refresh_token:
            creds = Credentials(
                token=None,  # Access Token은 나중에 Refresh Token으로 새로 얻을 것임
                refresh_token=self.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=SCOPES
            )
            # Refresh Token으로 Access Token 갱신
            try:
                creds.refresh(Request())
                logger.info("YouTube credentials refreshed successfully using refresh token.")
            except Exception as e:
                logger.error(f"Error refreshing YouTube credentials: {e}")
                # refresh_token이 유효하지 않은 경우, 수동으로 재인증해야 할 수 있습니다.
                raise Exception("Failed to refresh YouTube credentials. Please obtain a new refresh token.")
        else:
            logger.error("YouTube Refresh Token is not provided. Cannot authenticate.")
            raise ValueError("YouTube Refresh Token is missing. Please ensure YOUTUBE_REFRESH_TOKEN is set in secrets.")

        return creds

    def upload_video(self, video_file_path: str, title: str, description: str, tags: List[str], privacy_status: str = "private", thumbnail_file_path: str = None) -> str:
        """
        YouTube에 비디오를 업로드합니다.
        
        Args:
            video_file_path (str): 업로드할 비디오 파일의 로컬 경로.
            title (str): 비디오 제목.
            description (str): 비디오 설명.
            tags (List[str]): 비디오 태그 목록.
            privacy_status (str): 비디오 공개 상태 ('public', 'private', 'unlisted').
            thumbnail_file_path (str, optional): 업로드할 썸네일 파일의 로컬 경로.

        Returns:
            str: 업로드된 비디오의 ID (성공 시), 또는 None (실패 시).
        """
        try:
            youtube = build("youtube", "v3", credentials=self.credentials)

            body = {
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": tags,
                    "categoryId": "22",  # 'People & Blogs' 또는 적절한 카테고리 ID
                    "defaultLanguage": "ko"
                },
                "status": {
                    "privacyStatus": privacy_status,
                    "selfDeclaredMadeForKids": False # 아동용 콘텐츠가 아님
                }
            }

            # 비디오 파일 업로드
            media_body = MediaFileUpload(video_file_path, chunksize=-1, resumable=True)

            logger.info(f"Uploading video '{title}' from {video_file_path} to YouTube...")
            insert_request = youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media_body
            )

            # 비디오 업로드 진행 상황 모니터링 (선택 사항)
            response = None
            while response is None:
                status, response = insert_request.next_chunk()
                if status:
                    logger.info(f"Uploaded {int(status.resumable_progress * 100)}% of video.")
            
            video_id = response.get("id")
            logger.info(f"Video '{title}' successfully uploaded. Video ID: {video_id}")

            # 썸네일 업로드 (선택 사항)
            if thumbnail_file_path and os.path.exists(thumbnail_file_path):
                logger.info(f"Uploading thumbnail from {thumbnail_file_path} for video ID: {video_id}...")
                try:
                    thumbnail_media = MediaFileUpload(thumbnail_file_path)
                    youtube.thumbnails().set(
                        videoId=video_id,
                        media_body=thumbnail_media
                    ).execute()
                    logger.info(f"Thumbnail uploaded for video ID: {video_id}")
                except HttpError as e:
                    logger.error(f"Error uploading thumbnail: {e}")
                    # 썸네일 업로드 실패 시에도 비디오 업로드는 성공한 것으로 간주
            
            return video_id

        except HttpError as e:
            logger.error(f"An HTTP error {e.resp.status} occurred: {e.content.decode('utf-8')}")
            # API 쿼터 초과 등의 경우 에러 메시지 출력
            if e.resp.status == 403 and "quotaExceeded" in e.content.decode('utf-8'):
                logger.error("YouTube API Quota Exceeded. Please check your daily quota limits.")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during YouTube upload: {e}", exc_info=True)
            return None

# --- YouTube Refresh Token 발급을 위한 초기 인증 스크립트 (로컬에서 1회 실행) ---
# 이 코드는 Cloud Function에서 실행될 필요 없이, 개발 환경(Codespaces 또는 로컬)에서
# 최초 1회만 실행하여 refresh_token을 얻는 용도로 사용됩니다.
# 이 파일을 직접 실행할 때만 작동하도록 main 블록 안에 두었습니다.

if __name__ == "__main__":
    # 환경 변수에서 client_id와 client_secret을 로드 (로컬 테스트용)
    # 실제 배포 시에는 config.py를 통해 Secret Manager에서 로드됩니다.
    CLIENT_SECRETS_FILE = os.getenv("YOUTUBE_CLIENT_SECRETS_FILE", "client_secrets.json") # OAuth 클라이언트 비밀 파일
    
    # client_secrets.json 파일 생성 예시 (GCP 콘솔에서 OAuth 2.0 클라이언트 ID를 생성하여 다운로드)
    # {
    #   "web": {
    #     "client_id": "YOUR_CLIENT_ID",
    #     "project_id": "YOUR_PROJECT_ID",
    #     "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    #     "token_uri": "https://oauth2.googleapis.com/token",
    #     "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    #     "client_secret": "YOUR_CLIENT_SECRET",
    #     "redirect_uris": ["http://localhost:8080"]
    #   }
    # }

    if not os.path.exists(CLIENT_SECRETS_FILE):
        logger.warning(f"'{CLIENT_SECRETS_FILE}' not found. Please download your OAuth 2.0 Client ID JSON from GCP Console.")
        logger.warning("You can still run this script by setting YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET environment variables, but the initial token generation will require manual authorization in a browser.")
        # 환경 변수에서 직접 로드 시도 (GCP Secret Manager에서 로드되는 방식과 유사)
        local_client_id = os.getenv("YOUTUBE_CLIENT_ID_LOCAL") 
        local_client_secret = os.getenv("YOUTUBE_CLIENT_SECRET_LOCAL")

        if not local_client_id or not local_client_secret:
            logger.error("Cannot proceed without client_id and client_secret. Please set environment variables or create client_secrets.json.")
            exit(1)
        
        # client_secrets.json 파일 임시 생성 (refresh_token 발급용)
        temp_client_config = {
            "web": {
                "client_id": local_client_id,
                "project_id": "your-temp-project-id", # 임시 프로젝트 ID, 실제 사용되지 않음
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": local_client_secret,
                "redirect_uris": ["http://localhost:8080"]
            }
        }
        with open("temp_client_secrets.json", "w") as f:
            json.dump(temp_client_config, f, indent=4)
        CLIENT_SECRETS_FILE = "temp_client_secrets.json"
        logger.info(f"Temporary client secrets file created at {CLIENT_SECRETS_FILE}")

    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    
    # 로컬 서버를 통해 인증 코드 받기
    creds = flow.run_local_server(port=8080, success_message="Authentication successful! You can close this tab.")
    
    # refresh_token 저장 (이것을 GCP Secret Manager에 YOUTUBE_REFRESH_TOKEN으로 저장)
    if creds and creds.refresh_token:
        print("\n--- IMPORTANT ---")
        print("Your YouTube Refresh Token (Please copy this to GCP Secret Manager):")
        print(creds.refresh_token)
        print("--- IMPORTANT ---")
        logger.info("Refresh token obtained. Please save it to GCP Secret Manager as YOUTUBE_REFRESH_TOKEN.")
    else:
        logger.error("Failed to obtain refresh token. Please ensure proper authentication.")

    # 임시 파일이 생성되었다면 삭제
    if CLIENT_SECRETS_FILE == "temp_client_secrets.json" and os.path.exists("temp_client_secrets.json"):
        os.remove("temp_client_secrets.json")
        logger.info("Temporary client secrets file removed.")
