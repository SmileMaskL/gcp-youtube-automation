from googleapiclient.errors import HttpError
from src.monitoring import log_system_health
from src.youtube_uploader import get_authenticated_service # 인증 서비스 재활용

def post_comment(video_id, text_content):
    """
    특정 비디오에 댓글을 포스팅합니다.
    """
    youtube = get_authenticated_service()

    try:
        request = youtube.commentThreads().insert(
            part="snippet",
            body={
                "snippet": {
                    "videoId": video_id,
                    "topLevelComment": {
                        "snippet": {
                            "textOriginal": text_content
                        }
                    }
                }
            }
        )
        response = request.execute()
        log_system_health(f"댓글이 성공적으로 포스팅되었습니다. 댓글 ID: {response['id']}", level="info")
        return response
    except HttpError as e:
        # YouTube API 오류 코드에 따라 처리
        if e.resp.status == 403 and "commentsDisabled" in str(e.content):
            log_system_health(f"댓글 포스팅 실패: 비디오 '{video_id}'에 댓글이 비활성화되어 있습니다.", level="warning")
        else:
            log_system_health(f"댓글 포스팅 중 오류 발생: {e.resp.status}, {e.content.decode()}", level="error")
        raise ValueError(f"댓글 포스팅 실패: {e.content.decode()}")
    except Exception as e:
        log_system_health(f"댓글 포스팅 중 예상치 못한 오류 발생: {e}", level="error")
        raise ValueError(f"댓글 포스팅 실패: {e}")
