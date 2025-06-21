# src/comment_poster.py
import os
import logging
import httplib2
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"] # 댓글 작성 스코프

class CommentPoster:
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
                    logger.info("YouTube comment poster credentials refreshed successfully.")
                except Exception as e:
                    logger.error(f"Error refreshing YouTube comment poster access token: {e}")
                    raise Exception("Failed to refresh YouTube comment poster access token. Please check refresh token validity.")
            else:
                logger.error("Invalid or missing YouTube comment poster credentials. Please obtain a valid refresh token.")
                raise Exception("YouTube comment poster authentication failed. Refresh token might be invalid or expired.")
        
        try:
            return build("youtube", "v3", credentials=creds)
        except Exception as e:
            logger.error(f"Error building YouTube API service for comments: {e}")
            raise

    def post_comment(self, video_id: str, comment_text: str) -> bool:
        """
        지정된 비디오에 댓글을 작성합니다.
        """
        try:
            # 1. 댓글 스레드 생성 (최상위 댓글)
            insert_comment_thread = self.youtube.commentThreads().insert(
                part="snippet",
                body=dict(
                    snippet=dict(
                        videoId=video_id,
                        topLevelComment=dict(
                            snippet=dict(
                                textOriginal=comment_text
                            )
                        )
                    )
                )
            )
            response = insert_comment_thread.execute()
            logger.info(f"Comment '{comment_text}' posted successfully on video {video_id}.")
            return True

        except HttpError as e:
            logger.error(f"An HTTP error {e.resp.status} occurred when posting comment:\n{e.content.decode('utf-8')}")
            # 예를 들어, "comments disabled" 등의 오류 처리
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred during YouTube comment posting: {e}", exc_info=True)
            return False

if __name__ == "__main__":
    # 로컬 테스트를 위한 더미 설정 (실제 키는 사용하지 마세요!)
    temp_client_id = os.environ.get("YOUTUBE_CLIENT_ID_LOCAL", "YOUR_CLIENT_ID")
    temp_client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET_LOCAL", "YOUR_CLIENT_SECRET")
    temp_refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN_LOCAL", "YOUR_REFRESH_TOKEN")
    
    if "YOUR_CLIENT_ID" in temp_client_id or "YOUR_CLIENT_SECRET" in temp_client_secret or "YOUR_REFRESH_TOKEN" in temp_refresh_token:
        logger.warning("Please set YOUTUBE_CLIENT_ID_LOCAL, YOUTUBE_CLIENT_SECRET_LOCAL, YOUTUBE_REFRESH_TOKEN_LOCAL environment variables for local YouTube comment posting testing. Skipping local test.")
    else:
        # 실제 YouTube 영상 ID (테스트용)
        test_video_id = "YOUR_YOUTUBE_VIDEO_ID_HERE" # 실제 업로드된 영상 ID로 변경 필요
        if test_video_id == "YOUR_YOUTUBE_VIDEO_ID_HERE":
            logger.warning("Please set test_video_id to a real YouTube video ID for local comment posting testing.")
        else:
            comment_poster = CommentPoster(
                client_id=temp_client_id,
                client_secret=temp_client_secret,
                refresh_token=temp_refresh_token
            )
            comment = "이것은 자동화된 댓글 테스트입니다! 잘 작동하나요?"
            if comment_poster.post_comment(test_video_id, comment):
                print(f"로컬 테스트 댓글 작성 성공: {comment}")
            else:
                print("로컬 테스트 댓글 작성 실패.")
