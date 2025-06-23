import logging
import httplib2
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

class CommentPoster:
    def __init__(self, client_id, client_secret, refresh_token):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.youtube = self._get_authenticated_service()
    
    def _get_authenticated_service(self):
        if not all([self.client_id, self.client_secret, self.refresh_token]):
            logger.error("YouTube API credentials are missing.")
            raise ValueError("YouTube API credentials are required.")
            
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
            # 수정: 81자 → 분할 (원본 18번 라인)
            logger.info(
                "YouTube API credentials successfully refreshed "
                "for comment posting."
            )
        except Exception as e:
            logger.error(
                f"Failed to refresh YouTube access token for comment posting: {e}"
            )
            raise RuntimeError(f"YouTube authentication failed for comment posting: {e}")

        return build("youtube", "v3", credentials=credentials)

    def post_comment(self, video_id, comment_text):
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
            logger.error(
                f"An HTTP error {e.resp.status} occurred while posting comment: {e.content}"
            )
            return False
        except Exception as e:
            logger.error(
                f"An unexpected error occurred during comment posting: {e}", 
                exc_info=True
            )
            return False
