# src/comment_poster.py
import logging
from googleapiclient.discovery import build # F401 'googleapiclient.discovery.build' 사용되므로 유지
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class CommentPoster:
    def __init__(self, youtube_service):
        self.youtube = youtube_service
        logger.info("CommentPoster initialized.")

    def post_comment(self, video_id, text):
        """
        Posts a top-level comment to a YouTube video.
        """
        try:
            logger.info(f"Attempting to post comment to video {video_id}: {text[:50]}...")
            request = self.youtube.commentThreads().insert(
                part="snippet",
                body={
                    "snippet": {
                        "videoId": video_id,
                        "topLevelComment": {
                            "snippet": {
                                "textOriginal": text
                            }
                        }
                    }
                }
            )
            response = request.execute()
            logger.info(f"Comment posted successfully. Comment ID: {response['id']}")
            return response
        except HttpError as e:
            logger.error(f"Error posting comment: {e}", exc_info=True)
            if e.resp.status == 403:
                # E501 해결: 줄 길이를 79자 이하로 맞춤
                logger.error("Comment posting is disabled for this video "
                            "or channel, or API limit reached.")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred while posting comment: {e}",
                        exc_info=True)
            return None
    
