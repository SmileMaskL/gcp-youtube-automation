# src/youtube_utils.py
import os
import logging
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

logger = logging.getLogger(__name__)

# YouTube API 스코프 정의
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

class YouTubeUploader:
    """
    YouTube API를 사용하여 동영상을 업로드하고 관련 작업을 수행합니다.
    OAuth 2.0 자격 증명을 사용하여 인증합니다.
    """
    def __init__(self, oauth_credentials: dict):
        """
        Args:
            oauth_credentials (dict): client_id, client_secret, refresh_token을 포함하는 딕셔너리.
        """
        self.credentials = self._get_credentials(oauth_credentials)
        if self.credentials:
            self.youtube = build("youtube", "v3", credentials=self.credentials)
            logger.info("YouTube API client initialized.")
        else:
            logger.error("Failed to initialize YouTube API client due to missing credentials.")
            self.youtube = None

    def _get_credentials(self, oauth_credentials: dict):
        """
        제공된 OAuth 2.0 자격 증명 (client_id, client_secret, refresh_token)을 사용하여
        Google API Credentials 객체를 생성하고 유효성을 확인합니다.
        """
        if not all(k in oauth_credentials for k in ["client_id", "client_secret", "refresh_token"]):
            logger.error("Missing client_id, client_secret, or refresh_token in OAuth credentials.")
            return None

        try:
            creds = Credentials.from_authorized_user_info(
                info={
                    "client_id": oauth_credentials["client_id"],
                    "client_secret": oauth_credentials["client_secret"],
                    "refresh_token": oauth_credentials["refresh_token"],
                },
                scopes=SCOPES
            )
            # refresh_token을 사용하여 Access Token 갱신 시도
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                logger.info("YouTube API access token refreshed.")
            
            return creds
        except Exception as e:
            logger.error(f"Error loading YouTube OAuth credentials: {e}", exc_info=True)
            logger.error("Ensure YOUTUBE_OAUTH_CREDENTIALS secret contains valid client_id, client_secret, and refresh_token.")
            return None

    def upload_video(self, video_path: str, title: str, description: str, tags: list, category_id: str = "28", privacy_status: str = "public", thumbnail_path: str = None):
        """
        YouTube에 동영상을 업로드합니다.

        Args:
            video_path (str): 업로드할 동영상 파일의 경로.
            title (str): 동영상의 제목.
            description (str): 동영상의 설명.
            tags (list): 동영상의 태그 리스트.
            category_id (str): YouTube 카테고리 ID (기본값: 28 for Science & Technology).
            privacy_status (str): 동영상 공개 상태 ('public', 'private', 'unlisted').
            thumbnail_path (str, optional): 썸네일 이미지 파일의 경로.

        Returns:
            str: 업로드된 동영상의 YouTube URL, 실패 시 None.
        """
        if not self.youtube:
            logger.error("YouTube API client not initialized. Cannot upload video.")
            return None
        
        if not os.path.exists(video_path):
            logger.error(f"Video file not found at: {video_path}")
            return None

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": category_id,
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False, # 아동용 콘텐츠 여부
            },
            "processingStatus": {} # API 응답에서 처리 상태를 가져오기 위함
        }

        # 미디어 파일 준비
        media_body = MediaFileUpload(video_path, chunksize=-1, resumable=True)

        try:
            # 동영상 업로드 요청
            insert_request = self.youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media_body,
            )

            response = None
            while response is None:
                status, response = insert_request.next_chunk()
                if status:
                    logger.info(f"Uploaded {int(status.resumable_progress * 100)}% of {video_path}")

            video_id = response.get("id")
            video_url = f"https://youtu.be/{video_id}"
            logger.info(f"Video '{title}' uploaded to YouTube successfully! Video ID: {video_id}, URL: {video_url}")

            # 썸네일 업로드 (선택 사항)
            if thumbnail_path and os.path.exists(thumbnail_path):
                logger.info(f"Uploading thumbnail: {thumbnail_path}")
                try:
                    thumbnail_media = MediaFileUpload(thumbnail_path)
                    self.youtube.thumbnails().set(
                        videoId=video_id,
                        media_body=thumbnail_media
                    ).execute()
                    logger.info("Thumbnail uploaded successfully.")
                except HttpError as e:
                    logger.error(f"An HTTP error occurred during thumbnail upload: {e}", exc_info=True)
                except Exception as e:
                    logger.error(f"An unexpected error occurred during thumbnail upload: {e}", exc_info=True)
            elif thumbnail_path and not os.path.exists(thumbnail_path):
                logger.warning(f"Thumbnail file not found at: {thumbnail_path}. Skipping thumbnail upload.")

            # API 쿼터 사용량 모니터링 (대략적인 계산, 실제는 Google Cloud Metrics 확인)
            # video.insert는 약 1600 쿼터 비용 발생
            logger.info("YouTube API Quota usage: video.insert cost ~1600 units. Check Google Cloud Console for exact usage.")
            
            return video_url

        except HttpError as e:
            if e.resp.status == 403: # 권한 오류, API 쿼터 초과 등
                logger.error(f"YouTube API HttpError (Status: {e.resp.status}): {e.content.decode()}", exc_info=True)
                if "quotaExceeded" in e.content.decode():
                    logger.critical("YouTube API Daily Quota Exceeded! Please adjust schedule or apply for higher quota.")
                    # 쿼터 초과 시 다음 실행까지 대기하거나 관리자에게 알림
                elif "Forbidden" in e.content.decode() or "permissionDenied" in e.content.decode():
                    logger.critical("YouTube API Permission Denied! Check service account roles or OAuth scopes.")
            else:
                logger.error(f"An HTTP error occurred during video upload: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during video upload: {e}", exc_info=True)
            return None

    def post_comment(self, video_id: str, comment_text: str):
        """
        특정 동영상에 댓글을 작성합니다. (쿼터 비용 발생)

        Args:
            video_id (str): 댓글을 달 동영상의 ID.
            comment_text (str): 댓글 내용.

        Returns:
            bool: 성공 시 True, 실패 시 False.
        """
        if not self.youtube:
            logger.error("YouTube API client not initialized. Cannot post comment.")
            return False

        try:
            insert_request = self.youtube.commentThreads().insert(
                part="snippet",
                body={
                    "snippet": {
                        "videoId": video_id,
                        "topLevelComment": {
                            "snippet": {
                                "textOriginal": comment_text
                            }
                        }
                    }
                }
            )
            response = insert_request.execute()
            logger.info(f"Comment posted successfully on video {video_id}.")
            logger.info("YouTube API Quota usage: commentThreads.insert cost ~50 units.")
            return True
        except HttpError as e:
            logger.error(f"An HTTP error occurred during comment post: {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred during comment post: {e}", exc_info=True)
            return False

# 테스트용 코드 (로컬에서 YouTube API 인증 흐름 테스트)
# 이 부분은 로컬에서 refresh_token을 얻기 위해 한 번만 실행될 수 있습니다.
# 실제 Cloud Run Job에서는 필요 없습니다.
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv() # .env 파일 로드 (로컬 테스트용)
    from src.config import setup_logging, get_secret
    setup_logging()

    # 클라이언트 시크릿 파일 경로 (로컬에 저장된 credentials.json)
    # 구글 개발자 콘솔에서 OAuth 클라이언트 ID -> 데스크톱 앱 선택 후 다운로드한 JSON 파일
    CLIENT_SECRETS_FILE = "client_secrets.json" # 로컬에 이 파일을 생성해야 합니다.

    # 로컬에서 initial authorization flow를 위한 코드
    def get_authenticated_service():
        creds = None
        # 토큰 파일이 있으면 로드합니다.
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        # 토큰이 유효하지 않거나 없는 경우 로그인합니다.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(CLIENT_SECRETS_FILE):
                    print(f"Error: {CLIENT_SECRETS_FILE} not found.")
                    print("Please download your OAuth 2.0 Client ID (Desktop App) JSON from Google Cloud Console.")
                    print("Rename it to client_secrets.json and place it in the same directory.")
                    exit()
                flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            # 새 토큰을 저장합니다.
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        return creds

    # 로컬에서 실행하여 token.json을 생성하고, refresh_token을 얻은 후
    # 이를 사용하여 YOUTUBE_OAUTH_CREDENTIALS Secret Manager 값을 업데이트하세요.
    # creds = get_authenticated_service()
    # if creds:
    #     print("\n--- Your OAuth Credentials ---")
    #     print(f"Client ID: {creds.client_id}")
    #     print(f"Client Secret: {creds.client_secret}")
    #     print(f"Refresh Token: {creds.refresh_token}")
    #     print("\nCopy these values into YOUTUBE_OAUTH_CREDENTIALS in Secret Manager as a JSON string:")
    #     print(json.dumps({
    #         "client_id": creds.client_id,
    #         "client_secret": creds.client_secret,
    #         "refresh_token": creds.refresh_token
    #     }, indent=2))
    #     print("\n--- Local Upload Test (Requires real video/thumbnail files and valid credentials in Secret Manager) ---")
    #     # 실제 테스트는 Secret Manager에서 가져온 값으로 진행해야 합니다.
    #     # 아래는 예시이며, 실제 파일 경로와 Secret Manager 설정이 필요합니다.
    #     # try:
    #     #     oauth_creds_from_secret = json.loads(get_secret("YOUTUBE_OAUTH_CREDENTIALS", project_id=os.environ.get("GCP_PROJECT_ID")))
    #     #     uploader = YouTubeUploader(oauth_creds_from_secret)
    #     #     if uploader.youtube:
    #     #         test_video_path = "output/test_video.mp4" # 실제 파일 경로
    #     #         test_thumbnail_path = "output/test_thumbnail.jpg" # 실제 파일 경로
    #     #         if os.path.exists(test_video_path):
    #     #             video_url = uploader.upload_video(
    #     #                 test_video_path,
    #     #                 "Test Upload from Automation",
    #     #                 "This is a test video uploaded from automated pipeline.",
    #     #                 ["test", "automation", "shorts"],
    #     #                 thumbnail_path=test_thumbnail_path
    #     #             )
    #     #             if video_url:
    #     #                 print(f"Test video uploaded: {video_url}")
    #     #                 # uploader.post_comment(video_url.split('/')[-1], "Great video!")
    #     #             else:
    #     #                 print("Test video upload failed.")
    #     #         else:
    #     #             print(f"Test video file not found: {test_video_path}")
    #     #     else:
    #     #         print("YouTube Uploader not initialized due to credential issues.")
    #     # except Exception as e:
    #     #     print(f"Error during YouTube upload test: {e}")
    # else:
    #     print("Failed to get YouTube credentials.")
