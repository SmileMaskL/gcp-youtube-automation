import logging
from googleapiclient.errors import HttpError
from src.youtube_uploader import get_authenticated_service # 인증 서비스 재사용

logger = logging.getLogger(__name__)

def post_comment(video_id: str, comment_text: str, credentials_json_str: str):
    """
    지정된 YouTube 동영상에 댓글을 게시합니다.
    Args:
        video_id (str): 댓글을 게시할 동영상의 ID.
        comment_text (str): 게시할 댓글 내용.
        credentials_json_str (str): YouTube OAuth 2.0 클라이언트 ID JSON 문자열.
    Returns:
        bool: 댓글 게시 성공 여부.
    """
    if not video_id or not comment_text:
        logger.warning("Video ID or comment text is missing. Skipping comment post.")
        return False

    logger.info(f"Attempting to post comment to video ID: {video_id}")

    try:
        youtube = get_authenticated_service(credentials_json_str)

        # 댓글 스레드 생성 (최상위 댓글)
        request = youtube.commentThreads().insert(
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
        
        logger.info(f"Comment posted successfully to video ID {video_id}: '{comment_text}'")
        return True

    except HttpError as e:
        logger.error(f"HTTP error occurred while posting comment: {e.content.decode()}")
        if 'commentsDisabled' in e.content.decode():
            logger.warning(f"Comments are disabled for video ID {video_id}. Cannot post comment.")
        elif 'quotaExceeded' in e.content.decode():
            logger.critical("YouTube API Daily Quota Exceeded for comments. Cannot post more comments today.")
        else:
            logger.error("Unknown error during comment post. Check YouTube API settings.")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during comment post: {e}", exc_info=True)
        return False
