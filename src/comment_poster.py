import logging
import requests
import json # json 임포트 추가
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from .utils import get_secret # 상대 경로 임포트

logger = logging.getLogger(__name__)

def get_access_token():
    """액세스 토큰 갱신 (별도 함수로 분리)"""
    try:
        # Secret Manager에서 리프레시 토큰과 클라이언트 시크릿 불러오기
        refresh_token = get_secret("YOUTUBE_REFRESH_TOKEN")
        client_info = json.loads(get_secret("YOUTUBE_CLIENT_SECRET"))['installed']
        
        data = {
            'client_id': client_info['client_id'],
            'client_secret': client_info['client_secret'],
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token'
        }
        
        response = requests.post(
            client_info['token_uri'],
            data=data,
            timeout=15
        )
        response.raise_for_status() # HTTP 에러 발생 시 예외 처리
        return response.json()['access_token']
    except requests.exceptions.RequestException as req_e:
        logger.error(f"토큰 갱신 요청 실패: {req_e}")
        raise
    except json.JSONDecodeError as json_e:
        logger.error(f"YOUTUBE_CLIENT_SECRET 파싱 실패: {json_e}")
        raise
    except Exception as e:
        logger.error(f"토큰 갱신 일반 오류: {str(e)}")
        raise

def post_comment(video_id, text):
    """영상에 댓글 작성"""
    try:
        credentials = Credentials(token=get_access_token())
        youtube = build('youtube', 'v3', credentials=credentials)
        
        request_body = {
            "snippet": {
                "videoId": video_id,
                "topLevelComment": {
                    "snippet": {
                        "textOriginal": text
                    }
                }
            }
        }
        
        youtube.commentThreads().insert(
            part="snippet",
            body=request_body
        ).execute()
        
        logger.info(f"댓글 작성 성공: 영상 ID {video_id}")
        return True
    except Exception as e:
        logger.error(f"댓글 작성 실패 (영상 ID: {video_id}): {str(e)}")
        return False
