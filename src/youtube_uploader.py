# src/youtube_uploader.py
import os
import logging
import httplib2
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

logger = logging.getLogger(__name__)

# YouTube API 스코프 설정
SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube.force-ssl"]

class YouTubeUploader:
    def __init__(self, client_id: str, client_secret: str, refresh_token: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.youtube = self._authenticate_youtube()

    def _authenticate_youtube(self):
        """
        OAuth 2.0 Refresh Token을 사용하여 YouTube API 서비스 객체를 인증하고 반환합니다.
        """
        creds = None
        
        # Refresh Token을 사용하여 자격 증명 객체 생성
        # 실제 환경에서는 파일 대신 환경 변수나 Secret Manager에서 토큰을 가져옵니다.
        token_data = {
            "token": None,
            "refresh_token": self.refresh_token,
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scopes": SCOPES
        }
        creds = Credentials.from_authorized_user_info(token_data)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request(httplib2.Http()))
                    logger.info("YouTube credentials refreshed successfully.")
                except Exception as e:
                    logger.error(f"Error refreshing YouTube access token: {e}")
                    raise Exception("Failed to refresh YouTube access token. Please check refresh token validity.")
            else:
                logger.error("Invalid or missing YouTube credentials. Please obtain a valid refresh token.")
                raise Exception("YouTube authentication failed. Refresh token might be invalid or expired.")
        
        try:
            return build("youtube", "v3", credentials=creds)
        except Exception as e:
            logger.error(f"Error building YouTube API service: {e}")
            raise

    def upload_video(self, video_file_path: str, title: str, description: str, tags: list, privacy_status: str = "private", thumbnail_file_path: str = None) -> Union[str, None]:
        """
        지정된 비디오 파일을 YouTube에 업로드합니다.
        """
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

        # MediaFileUpload 객체 생성
        media_body = MediaFileUpload(video_file_path, chunksize=-1, resumable=True)

        try:
            insert_request = self.youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media_body
            )

            response = None
            while response is None:
                status, response = insert_request.next_chunk()
                if status:
                    logger.info(f"Uploaded {int(status.progress() * 100)}% of video.")
            
            video_id = response.get("id")
            logger.info(f"Video '{title}' uploaded. Video ID: {video_id}")

            # 썸네일 업로드
            if thumbnail_file_path and os.path.exists(thumbnail_file_path):
                logger.info(f"Uploading thumbnail for video ID: {video_id}")
                try:
                    thumbnail_media = MediaFileUpload(thumbnail_file_path)
                    self.youtube.thumbnails().set(
                        videoId=video_id,
                        media_body=thumbnail_media
                    ).execute()
                    logger.info("Thumbnail uploaded successfully.")
                except HttpError as e:
                    logger.warning(f"Could not set thumbnail: {e}")
                    logger.warning("Thumbnail upload is often rate-limited or requires specific channel permissions. Proceeding without thumbnail.")
                except Exception as e:
                    logger.warning(f"An unexpected error occurred during thumbnail upload: {e}")
            else:
                logger.info("No thumbnail file provided or found. Skipping thumbnail upload.")

            return video_id

        except HttpError as e:
            logger.error(f"An HTTP error {e.resp.status} occurred:\n{e.content.decode('utf-8')}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during YouTube video upload: {e}", exc_info=True)
            return None

if __name__ == "__main__":
    # 로컬 테스트를 위한 더미 설정 (실제 키는 사용하지 마세요!)
    # 이 테스트는 실제 YouTube 계정에 업로드되므로 주의해야 합니다.
    # 먼저 YouTube API에 대한 OAuth 2.0 웹 클라이언트 ID와 시크릿을 생성하고,
    # refresh_token을 수동으로 얻어야 합니다. (oauth2.py 등 별도 스크립트 필요)

    temp_client_id = os.environ.get("YOUTUBE_CLIENT_ID_LOCAL", "YOUR_CLIENT_ID")
    temp_client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET_LOCAL", "YOUR_CLIENT_SECRET")
    temp_refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN_LOCAL", "YOUR_REFRESH_TOKEN")

    if "YOUR_CLIENT_ID" in temp_client_id or "YOUR_CLIENT_SECRET" in temp_client_secret or "YOUR_REFRESH_TOKEN" in temp_refresh_token:
        logger.warning("Please set YOUTUBE_CLIENT_ID_LOCAL, YOUTUBE_CLIENT_SECRET_LOCAL, YOUTUBE_REFRESH_TOKEN_LOCAL environment variables for local YouTube upload testing. Skipping local test.")
    else:
        # 가짜 영상 파일 생성 (실제 파일을 사용하거나 moviepy 등으로 생성)
        dummy_video_path = "output/dummy_video.mp4"
        if not os.path.exists("output"):
            os.makedirs("output")
        with open(dummy_video_path, "wb") as f:
            f.write(b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom\x00\x00\x00\x00")
        
        # 가짜 썸네일 파일 생성
        dummy_thumbnail_path = "output/dummy_thumbnail.jpg"
        from PIL import Image
        img = Image.new('RGB', (1280, 720), color = 'red')
        img.save(dummy_thumbnail_path)

        uploader = YouTubeUploader(
            client_id=temp_client_id,
            client_secret=temp_client_secret,
            refresh_token=temp_refresh_token
        )
        
        uploaded_video_id = uploader.upload_video(
            video_file_path=dummy_video_path,
            title="테스트 영상 업로드 (자동화)",
            description="이것은 YouTube Shorts 자동화 시스템 테스트 영상입니다.",
            tags=["테스트", "자동화", "유튜브"],
            privacy_status="private", # 테스트용이므로 private으로 업로드
            thumbnail_file_path=dummy_thumbnail_path
        )
        
        if uploaded_video_id:
            print(f"로컬 테스트 영상 업로드 성공: https://www.youtube.com/watch?v={uploaded_video_id}")
        else:
            print("로컬 테스트 영상 업로드 실패.")

        os.remove(dummy_video_path)
        os.remove(dummy_thumbnail_path)
