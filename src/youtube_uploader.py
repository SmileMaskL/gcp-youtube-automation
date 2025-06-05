import os
import json
import time
import requests
import logging
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from .utils import get_secret # utils에서 get_secret 임포트
from .comment_poster import post_comment # comment_poster에서 post_comment 임포트

logger = logging.getLogger(__name__)

def load_refresh_token():
    """Secret Manager에서 리프레시 토큰 불러오기"""
    try:
        return get_secret("YOUTUBE_REFRESH_TOKEN")
    except Exception as e:
        logger.error(f"YOUTUBE_REFRESH_TOKEN 로드 실패: {e}")
        raise

def load_client_secrets():
    """Secret Manager에서 클라이언트 시크릿 불러오기"""
    try:
        return json.loads(get_secret("YOUTUBE_CLIENT_SECRET"))
    except json.JSONDecodeError as e:
        logger.error(f"YOUTUBE_CLIENT_SECRET JSON 파싱 실패: {e}")
        raise
    except Exception as e:
        logger.error(f"YOUTUBE_CLIENT_SECRET 로드 실패: {e}")
        raise

def get_access_token():
    """액세스 토큰 갱신"""
    try:
        refresh_token = load_refresh_token()
        client_info = load_client_secrets()['installed']
        
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
        response.raise_for_status()
        access_token_data = response.json()
        
        # 새로운 리프레시 토큰이 있다면 업데이트 (선택 사항, 필요 시 Secret Manager 업데이트 로직 추가)
        if 'refresh_token' in access_token_data:
            # 이 부분은 Secret Manager에 새로운 refresh token을 업데이트하는 로직이 필요.
            # 하지만 Secret Manager 업데이트 API 호출은 추가 권한이 필요하고 복잡하므로,
            # 만료 기간이 긴 리프레시 토큰을 수동으로 갱신하는 것이 일반적입니다.
            logger.warning("새로운 리프레시 토큰이 발급되었으나 Secret Manager에 자동 업데이트되지 않았습니다.")
            
        return access_token_data['access_token']
    except requests.exceptions.RequestException as req_e:
        logger.error(f"토큰 갱신 요청 실패: {req_e}")
        raise
    except Exception as e:
        logger.error(f"토큰 갱신 일반 오류: {str(e)}\n{traceback.format_exc()}")
        raise

def upload_video(file_path, title, description, thumbnail_path=None):
    """유튜브 업로드 + 썸네일 설정 + 댓글 작성"""
    if not os.path.exists(file_path):
        logger.error(f"업로드 실패: 영상 파일이 존재하지 않습니다. {file_path}")
        raise FileNotFoundError(f"영상 파일이 존재하지 않습니다: {file_path}")

    try:
        credentials = Credentials(token=get_access_token())
        youtube = build('youtube', 'v3', credentials=credentials)
        
        # 비디오 메타데이터 설정
        request_body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': ['AI', '자동화', 'Shorts', '최신트렌드', '수익창출'], # 태그 추가
                'categoryId': '28', # Science & Technology
                'defaultLanguage': 'ko', # 기본 언어 한국어로 설정
                'localized': { # 지역별 제목 및 설명 (선택 사항, 복잡해질 수 있음)
                    'ko': {'title': title, 'description': description}
                }
            },
            'status': {
                'privacyStatus': 'public', # 'private' for testing
                'selfDeclaredMadeForKids': False,
                'embeddable': True, # 임베딩 허용
                'publicStatsViewable': True # 공개 통계 허용
            }
        }
        
        # 비디오 업로드
        media_file = MediaFileUpload(file_path, resumable=True)
        request = youtube.videos().insert(
            part='snippet,status',
            body=request_body,
            media_body=media_file
        )
        
        # 업로드 진행 상황 모니터링 (실제 배포 환경에서는 잘 안 보일 수 있음)
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logger.info(f"업로드 진행: {int(status.progress() * 100)}%")
        
        video_id = response['id']
        logger.info(f"✅ 업로드 완료! 영상 ID: {video_id}")
        
        # 썸네일 설정
        if thumbnail_path and os.path.exists(thumbnail_path):
            try:
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(thumbnail_path)
                ).execute()
                logger.info(f"썸네일 설정 완료: {thumbnail_path}")
            except Exception as e:
                logger.error(f"썸네일 설정 실패 (영상 ID: {video_id}): {str(e)}")
        else:
            logger.warning(f"썸네일 경로가 유효하지 않거나 파일이 없습니다: {thumbnail_path}")

        # 댓글 작성은 app.py에서 별도로 호출
        # post_comment(video_id, "이 영상은 AI로 자동 생성되었습니다! 구독 부탁드려요 :)")
        # logger.info(f"댓글 작성 완료: {video_id}")
        
        return f"https://www.youtube.com/watch?v={video_id}" # 유튜브 영상 URL 반환
        
    except Exception as e:
        logger.error(f"🔴 유튜브 업로드 실패: {str(e)}\n{traceback.format_exc()}")
        raise # 업로드 실패 시 예외 발생
