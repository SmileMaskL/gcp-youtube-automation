# src/comment_poster.py
import httplib2
import logging
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"] # 댓글 작성 스코프

class CommentPoster:
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
            
        credentials = Credentials(
            token=None,
            refresh_token=self.refresh_token,
            client_id=self.client_id,
            client_secret=self.client_secret,
            token_uri="https://oauth2.googleapis.com/token",
            scopes=SCOPES
        )

        try:
            credentials.refresh(httplib2.Http())
            logger.info("YouTube API credentials successfully refreshed for comment posting.")
        except Exception as e:
            logger.error(f"Failed to refresh YouTube access token for comment posting: {e}")
            raise RuntimeError(f"YouTube authentication failed for comment posting: {e}")

        return build("youtube", "v3", credentials=credentials)

    def post_comment(self, video_id, comment_text):
        """지정된 영상에 댓글을 작성합니다."""
        try:
            request = self.youtube.commentThreads().insert(
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
            response = request.execute()
            logger.info(f"Comment posted: {comment_text}")
            return True
        except HttpError as e:
            logger.error(f"An HTTP error {e.resp.status} occurred while posting comment: {e.content}")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred during comment posting: {e}", exc_info=True)
            return False
