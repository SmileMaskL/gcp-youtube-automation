# src/youtube_uploader.py
import logging
import os
import http.client
import httplib2
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from oauth2client.client import OAuth2Credentials

logger = logging.getLogger(__name__)

# Constants
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

class YouTubeUploader:
    def __init__(self, client_id, client_secret, refresh_token):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.youtube_service = self._authenticate_youtube()
        logger.info("YouTubeUploader initialized and authenticated.")

    def _authenticate_youtube(self):
        """
        OAuth 2.0 Refresh Token을 사용하여 YouTube API 서비스에 인증합니다.
        """
        if not all([self.client_id, self.client_secret, self.refresh_token]):
            logger.error("Missing YouTube client ID, client secret, or refresh token.")
            raise ValueError("YouTube authentication credentials missing.")

        try:
            # OAuth2Credentials 객체 생성
            credentials = OAuth2Credentials(
                access_token=None,  # refresh token으로 access token을 새로 받으므로 None
                client_id=self.client_id,
                client_secret=self.client_secret,
                refresh_token=self.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                user_agent="YouTube-Automation-Script/1.0"
            )
            
            # credentials.authorize(httplib2.Http())를 사용하여 access token 새로고침
            # 이 과정에서 내부적으로 refresh token을 사용하여 새로운 access token을 얻습니다.
            http = credentials.authorize(httplib2.Http())
            
            # 인증된 HTTP 클라이언트로 YouTube 서비스 빌드
            youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, http=http)
            logger.info("YouTube service built successfully with refresh token.")
            return youtube
        except HttpError as e:
            logger.error(f"HTTP error during YouTube authentication: {e.resp.status} - {e.content}", exc_info=True)
            if e.resp.status == 401:
                logger.error("Refresh token might be expired or invalid. Please re-authenticate.")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred during YouTube authentication: {e}", exc_info=True)
            raise

    def upload_video(self, file_path, title, description, keywords, privacy_status="private"):
        """
        YouTube에 비디오를 업로드합니다.
        """
        if not self.youtube_service:
            logger.error("YouTube service not authenticated. Cannot upload video.")
            return None

        if not os.path.exists(file_path):
            logger.error(f"Video file not found: {file_path}")
            return None

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": keywords,
                "categoryId": "22",  # Entertainment Category (Shorts usually fit here or People & Blogs)
                "defaultLanguage": "ko" # 한국어
            },
            "status": {
                "privacyStatus": privacy_status, # "public", "private", "unlisted"
                "selfDeclaredMadeForKids": False # 아동용 콘텐츠가 아님을 선언
            },
            "recordingDetails": {
                "recordingDate": None # 선택 사항, 필요한 경우 추가
            }
        }

        # 미디어 파일 업로드 설정
        media_body = MediaFileUpload(file_path, chunksize=-1, resumable=True)

        try:
            # YouTube API 호출하여 비디오 업로드
            request = self.youtube_service.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media_body
            )
            response = None
            
            # Resumable upload (큰 파일에 유용)
            while response is None:
                status, response = request.next_chunk()
                if status:
                    logger.info(f"Uploaded {int(status.progress() * 100)}% of {file_path}")

            if response:
                video_id = response.get("id")
                logger.info(f"Video uploaded successfully! Video ID: {video_id}")
                logger.info(f"Video URL: https://www.youtube.com/watch?v={video_id}")
                return video_id
            else:
                logger.error("Video upload failed: No response received.")
                return None

        except HttpError as e:
            logger.error(f"HTTP error during video upload: {e.resp.status} - {e.content}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during video upload: {e}", exc_info=True)
            return None

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    # 로컬 테스트를 위한 환경 변수 로드 (실제 배포에서는 Cloud Run에서 전달됨)
    TEST_CLIENT_ID = os.environ.get("YOUTUBE_CLIENT_ID")
    TEST_CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET")
    TEST_REFRESH_TOKEN = os.environ.get("YOUTUBE_REFRESH_TOKEN")

    if not all([TEST_CLIENT_ID, TEST_CLIENT_SECRET, TEST_REFRESH_TOKEN]):
        logger.warning("YouTube API credentials not found in environment variables. Cannot run local test.")
        logger.info("Please set YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN.")
    else:
        # 가상의 비디오 파일 생성 (실제 테스트 시에는 유효한 파일 경로로 변경)
        dummy_video_path = "temp_shorts_video.mp4"
        with open(dummy_video_path, "w") as f:
            f.write("This is a dummy video file for testing.")

        uploader = YouTubeUploader(TEST_CLIENT_ID, TEST_CLIENT_SECRET, TEST_REFRESH_TOKEN)
        
        test_title = "Test AI Shorts Upload"
        test_description = "This is a test video uploaded by an automated AI script."
        test_keywords = ["AI", "shorts", "automation", "test"]

        # 실제 업로드 실행 (privacy_status를 "private"으로 설정하여 비공개 업로드)
        uploaded_video_id = uploader.upload_video(
            dummy_video_path, 
            test_title, 
            test_description, 
            test_keywords, 
            privacy_status="private"
        )
        if uploaded_video_id:
            logger.info(f"Dummy video uploaded with ID: {uploaded_video_id}")
        else:
            logger.error("Failed to upload dummy video.")
        
        # 테스트 파일 정리
        if os.path.exists(dummy_video_path):
            os.remove(dummy_video_path)
