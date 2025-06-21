# src/comment_poster.py
import logging
import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# 승인된 범위 정의 (유튜브 댓글 작성 권한)
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"] # 또는 youtube.comment, 하지만 force-ssl이 일반적으로 더 넓은 권한을 포함

class CommentPoster:
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
        if self.refresh_token:
            creds = Credentials(
                token=None,
                refresh_token=self.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=SCOPES
            )
            try:
                creds.refresh(Request())
                logger.info("YouTube credentials refreshed successfully for comment posting.")
            except Exception as e:
                logger.error(f"Error refreshing YouTube credentials for comment posting: {e}")
                raise Exception("Failed to refresh YouTube credentials. Please obtain a new refresh token.")
        else:
            logger.error("YouTube Refresh Token is not provided. Cannot authenticate for comment posting.")
            raise ValueError("YouTube Refresh Token is missing.")
        return creds

    def post_comment(self, video_id: str, comment_text: str) -> bool:
        """
        특정 비디오에 댓글을 게시합니다.
        """
        try:
            youtube = build("youtube", "v3", credentials=self.credentials)

            comment_thread_body = {
                "snippet": {
                    "videoId": video_id,
                    "topLevelComment": {
                        "snippet": {
                            "textOriginal": comment_text
                        }
                    }
                }
            }

            request = youtube.commentThreads().insert(
                part="snippet",
                body=comment_thread_body
            )
            response = request.execute()
            logger.info(f"Comment successfully posted to video ID {video_id}: '{comment_text}'")
            return True

        except HttpError as e:
            logger.error(f"An HTTP error {e.resp.status} occurred while posting comment: {e.content.decode('utf-8')}")
            if e.resp.status == 403 and "commentsDisabled" in e.content.decode('utf-8'):
                logger.warning(f"Comments are disabled for video ID: {video_id}. Cannot post comment.")
            elif e.resp.status == 403 and "quotaExceeded" in e.content.decode('utf-8'):
                logger.error("YouTube API Quota Exceeded for comment posting.")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred while posting comment: {e}", exc_info=True)
            return False
