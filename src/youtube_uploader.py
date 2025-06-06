import os
import json
import time
import logging
import traceback
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from .utils import get_secret  # Secret Manager 연동

logger = logging.getLogger(__name__)

def upload_video(file_path, title, description, thumbnail_path=None):
    """실전용 업로드 (서비스 계정 + OAuth 통합)"""
    # 1. 서비스 계정 인증 시도 (우선순위)
    try:
        service_account_json = json.loads(get_secret("GCP_SERVICE_ACCOUNT_KEY"))
        credentials = service_account.Credentials.from_service_account_info(
            service_account_json,
            scopes=['https://www.googleapis.com/auth/youtube.upload']
        )
        logger.info("✅ 서비스 계정 인증 사용")
        
    except Exception as sa_error:
        logger.warning(f"⚠️ 서비스 계정 실패: {sa_error}. OAuth로 전환")
        # OAuth 인증 로직 (기존 코드 활용)
        try:
            # ... [기존 load_refresh_token(), get_access_token() 코드] ...
            credentials = Credentials(token=access_token)
        except Exception as oauth_error:
            logger.error(f"🔴 OAuth 인증 실패: {oauth_error}")
            raise RuntimeError("모든 인증 수단 실패")

    # 2. 업로드 실행 (3회 재시도)
    youtube = build('youtube', 'v3', credentials=credentials)
    for attempt in range(3):
        try:
            # 메타데이터 설정
            body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'tags': ['AI자동생성', 'Shorts', '수익창출'],
                    'categoryId': '22',
                    'defaultLanguage': 'ko'
                },
                'status': {
                    'privacyStatus': 'public',
                    'publishAt': (datetime.now() + timedelta(minutes=10)).isoformat() + "Z",
                    'selfDeclaredMadeForKids': False
                }
            }
            
            # 미디어 파일 준비
            media = MediaFileUpload(file_path, resumable=True)
            
            # 업로드 요청
            request = youtube.videos().insert(
                part='snippet,status',
                body=body,
                media_body=media
            )
            
            # 업로드 진행 모니터링
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    logger.info(f"진행률: {int(status.progress() * 100)}%")
            
            video_id = response['id']
            logger.info(f"✅ 업로드 성공! 영상 ID: {video_id}")
            
            # 3. 썸네일 업로드
            if thumbnail_path and os.path.exists(thumbnail_path):
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(thumbnail_path)
                ).execute()
                logger.info(f"🖼️ 썸네일 업로드 완료")
            
            return f"https://www.youtube.com/watch?v={video_id}"
            
        except HttpError as e:
            if e.resp.status in [500, 502, 503, 504]:
                wait_time = 2 ** attempt  # 지수 백오프
                logger.warning(f"🔄 서버 오류 ({e.resp.status}), {wait_time}초 후 재시도...")
                time.sleep(wait_time)
            else:
                logger.error(f"🔴 치명적 오류: {e.resp.status}")
                raise
        except Exception as e:
            logger.error(f"🔴 업로드 실패: {str(e)}\n{traceback.format_exc()}")
            if attempt == 2:  # 마지막 시도에서도 실패
                raise RuntimeError("업로드 3회 연속 실패")
            time.sleep(3)
    
    return None  # 모든 시도 실패
    
    except:
        logger.warning("⚠️ 채널 수익화 미승인 상태")
